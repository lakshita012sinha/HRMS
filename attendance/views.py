from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db import transaction
from datetime import datetime, date
from .models import (
    Shift, EmployeeShiftAssignment, Holiday, Attendance,
    AttendanceLog, GeoTracking, AttendanceRegularization
)
from .serializers import (
    ShiftSerializer, EmployeeShiftAssignmentSerializer, HolidaySerializer,
    AttendanceSerializer, AttendanceLogSerializer, CheckInSerializer,
    CheckOutSerializer, AttendanceRegularizationSerializer,
    ApproveRegularizationSerializer, GeoTrackingSerializer,
    BulkAttendanceSerializer
)
import calendar as cal
from accounts.models import User


# Shift Management
class ShiftListCreateView(generics.ListCreateAPIView):
    """List and create shifts"""
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [permissions.IsAuthenticated]


class ShiftDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete shift"""
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [permissions.IsAuthenticated]


# Employee Shift Assignment
class EmployeeShiftAssignmentListCreateView(generics.ListCreateAPIView):
    """List and create employee shift assignments"""
    queryset = EmployeeShiftAssignment.objects.all()
    serializer_class = EmployeeShiftAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = EmployeeShiftAssignment.objects.all()
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        return queryset


class EmployeeShiftAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete shift assignment"""
    queryset = EmployeeShiftAssignment.objects.all()
    serializer_class = EmployeeShiftAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]


# Holiday Management
class HolidayListCreateView(generics.ListCreateAPIView):
    """List and create holidays"""
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer
    permission_classes = [permissions.IsAuthenticated]


class HolidayDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete holiday"""
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer
    permission_classes = [permissions.IsAuthenticated]


# Attendance Check-in/Check-out
class CheckInView(APIView):
    """Employee check-in with GPS tracking"""
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        employee = request.user
        today = date.today()
        
        # Check if already checked in today
        existing_log = AttendanceLog.objects.filter(
            employee=employee,
            timestamp__date=today,
            log_type='CHECK_IN'
        ).first()
        
        if existing_log:
            return Response(
                {'error': 'Already checked in today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create attendance record
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={'status': 'PRESENT'}
        )
        
        # Create check-in log
        check_in_time = timezone.now()
        attendance_log = AttendanceLog.objects.create(
            employee=employee,
            attendance=attendance,
            timestamp=check_in_time,
            log_type='CHECK_IN',
            location=serializer.validated_data.get('address', ''),
            device=serializer.validated_data.get('device', ''),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Create GPS tracking
        GeoTracking.objects.create(
            attendance_log=attendance_log,
            latitude=serializer.validated_data['latitude'],
            longitude=serializer.validated_data['longitude'],
            address=serializer.validated_data.get('address', ''),
            accuracy=serializer.validated_data.get('accuracy', 0)
        )
        
        # Update attendance
        attendance.check_in_time = check_in_time
        attendance.location = serializer.validated_data.get('address', '')
        attendance.status = 'PRESENT'
        attendance.save()
        
        return Response({
            'message': 'Checked in successfully',
            'attendance': AttendanceSerializer(attendance).data,
            'log': AttendanceLogSerializer(attendance_log).data
        }, status=status.HTTP_201_CREATED)


class CheckOutView(APIView):
    """Employee check-out with GPS tracking"""
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        serializer = CheckOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        employee = request.user
        today = date.today()
        
        # Get today's attendance
        try:
            attendance = Attendance.objects.get(employee=employee, date=today)
        except Attendance.DoesNotExist:
            return Response(
                {'error': 'No check-in found for today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already checked out
        if attendance.check_out_time:
            return Response(
                {'error': 'Already checked out today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create check-out log
        check_out_time = timezone.now()
        attendance_log = AttendanceLog.objects.create(
            employee=employee,
            attendance=attendance,
            timestamp=check_out_time,
            log_type='CHECK_OUT',
            location=serializer.validated_data.get('address', ''),
            device=serializer.validated_data.get('device', ''),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Create GPS tracking
        GeoTracking.objects.create(
            attendance_log=attendance_log,
            latitude=serializer.validated_data['latitude'],
            longitude=serializer.validated_data['longitude'],
            address=serializer.validated_data.get('address', ''),
            accuracy=serializer.validated_data.get('accuracy', 0)
        )
        
        # Update attendance
        attendance.check_out_time = check_out_time
        attendance.calculate_total_hours()
        attendance.save()
        
        return Response({
            'message': 'Checked out successfully',
            'attendance': AttendanceSerializer(attendance).data,
            'log': AttendanceLogSerializer(attendance_log).data
        }, status=status.HTTP_200_OK)


# Break Management
class BreakStartView(APIView):
    """Start break"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        employee = request.user
        today = date.today()
        
        try:
            attendance = Attendance.objects.get(employee=employee, date=today)
        except Attendance.DoesNotExist:
            return Response(
                {'error': 'No check-in found for today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create break start log
        attendance_log = AttendanceLog.objects.create(
            employee=employee,
            attendance=attendance,
            timestamp=timezone.now(),
            log_type='BREAK_START',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            'message': 'Break started',
            'log': AttendanceLogSerializer(attendance_log).data
        }, status=status.HTTP_201_CREATED)


class BreakEndView(APIView):
    """End break"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        employee = request.user
        today = date.today()
        
        try:
            attendance = Attendance.objects.get(employee=employee, date=today)
        except Attendance.DoesNotExist:
            return Response(
                {'error': 'No check-in found for today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create break end log
        attendance_log = AttendanceLog.objects.create(
            employee=employee,
            attendance=attendance,
            timestamp=timezone.now(),
            log_type='BREAK_END',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            'message': 'Break ended',
            'log': AttendanceLogSerializer(attendance_log).data
        }, status=status.HTTP_201_CREATED)


# Attendance Management
class AttendanceListView(generics.ListAPIView):
    """List attendance records"""
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Attendance.objects.all()
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        elif user.role and user.role.name not in ['HR', 'ADMIN']:
            # Non-HR/Admin can only see their own attendance
            queryset = queryset.filter(employee=user)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-date')


class AttendanceDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve and update attendance"""
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]


class MyAttendanceView(APIView):
    """Get current user's attendance for today"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        today = date.today()
        try:
            attendance = Attendance.objects.get(employee=request.user, date=today)
            return Response(AttendanceSerializer(attendance).data)
        except Attendance.DoesNotExist:
            return Response({
                'message': 'No attendance record for today',
                'date': today
            }, status=status.HTTP_404_NOT_FOUND)


# Attendance Logs
class AttendanceLogListView(generics.ListAPIView):
    """List attendance logs"""
    serializer_class = AttendanceLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = AttendanceLog.objects.all()
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        elif user.role and user.role.name not in ['HR', 'ADMIN']:
            queryset = queryset.filter(employee=user)
        
        # Filter by date
        date_filter = self.request.query_params.get('date', None)
        if date_filter:
            queryset = queryset.filter(timestamp__date=date_filter)
        
        return queryset.order_by('-timestamp')


# Attendance Regularization
class AttendanceRegularizationListCreateView(generics.ListCreateAPIView):
    """List and create regularization requests"""
    serializer_class = AttendanceRegularizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role and user.role.name in ['HR', 'ADMIN']:
            return AttendanceRegularization.objects.all()
        return AttendanceRegularization.objects.filter(employee=user)
    
    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)


class AttendanceRegularizationDetailView(generics.RetrieveAPIView):
    """Retrieve regularization request"""
    queryset = AttendanceRegularization.objects.all()
    serializer_class = AttendanceRegularizationSerializer
    permission_classes = [permissions.IsAuthenticated]


class ApproveRegularizationView(APIView):
    """Approve or reject regularization request"""
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, pk):
        # Only HR/Admin can approve
        if not request.user.role or request.user.role.name not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR and Admin can approve regularizations'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            regularization = AttendanceRegularization.objects.get(pk=pk)
        except AttendanceRegularization.DoesNotExist:
            return Response(
                {'error': 'Regularization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ApproveRegularizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        regularization.status = serializer.validated_data['status']
        regularization.approved_by = request.user
        regularization.approved_at = timezone.now()
        
        if serializer.validated_data['status'] == 'APPROVED':
            # Update attendance record
            attendance = regularization.attendance
            attendance.check_in_time = regularization.requested_check_in
            attendance.check_out_time = regularization.requested_check_out
            attendance.calculate_total_hours()
            attendance.status = 'PRESENT'
            attendance.save()
        else:
            regularization.rejection_reason = serializer.validated_data.get('rejection_reason', '')
        
        regularization.save()
        
        return Response({
            'message': f'Regularization {serializer.validated_data["status"].lower()}',
            'regularization': AttendanceRegularizationSerializer(regularization).data
        }, status=status.HTTP_200_OK)


class MonthlyAttendanceView(APIView):
    """Get all employees' attendance for a given month/year (HR view)"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        is_hr = request.user.role and request.user.role.name in ['HR', 'ADMIN']

        month = int(request.query_params.get('month', date.today().month))
        year  = int(request.query_params.get('year',  date.today().year))

        days_in_month = cal.monthrange(year, month)[1]

        # HR/Admin see all employees; others see only themselves
        if is_hr:
            employees = User.objects.filter(is_active=True).exclude(role__name__in=['ADMIN'])
        else:
            employees = User.objects.filter(id=request.user.id)

        # Holidays in this month
        holidays = set(Holiday.objects.filter(date__year=year, date__month=month).values_list('date', flat=True))

        # All attendance records for this month
        att_qs = Attendance.objects.filter(date__year=year, date__month=month).select_related('employee')
        att_map = {}  # (employee_id, date) -> status
        for a in att_qs:
            att_map[(a.employee_id, a.date)] = a.status

        result = []
        for emp in employees:
            days = {}
            present = absent = holiday_count = sunday_count = leave_count = half_day = 0
            for d in range(1, days_in_month + 1):
                dt = date(year, month, d)
                weekday = dt.weekday()  # 6 = Sunday
                if weekday == 6:
                    days[d] = 'OFF'
                    sunday_count += 1
                elif dt in holidays:
                    days[d] = 'H'
                    holiday_count += 1
                else:
                    att_status = att_map.get((emp.id, dt))
                    if att_status == 'PRESENT':
                        days[d] = 'P'; present += 1
                    elif att_status == 'HALF_DAY':
                        days[d] = 'HDP'; half_day += 1; present += 0.5
                    elif att_status == 'LEAVE':
                        days[d] = 'L'; leave_count += 1
                    elif att_status == 'ABSENT':
                        days[d] = 'A'; absent += 1
                    else:
                        days[d] = ''  # not marked yet

            pay_days = present + sunday_count
            result.append({
                'employee_id': emp.id,
                'user_id': emp.user_id,
                'name': f"{emp.first_name} {emp.last_name}".strip().upper(),
                'days': days,
                'present': present,
                'absent': absent,
                'holiday': holiday_count,
                'sunday': sunday_count,
                'leave': leave_count,
                'half_day': half_day,
                'pay_days': pay_days,
                'days_in_month': days_in_month,
            })

        return Response({'month': month, 'year': year, 'days_in_month': days_in_month, 'employees': result})


class BulkMarkAttendanceView(APIView):
    """HR marks/updates attendance for one employee on one date"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        if not request.user.role or request.user.role.name not in ['HR', 'ADMIN']:
            return Response({'error': 'Only HR and Admin can mark attendance'}, status=status.HTTP_403_FORBIDDEN)

        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        employee_id = serializer.validated_data['employee_id']
        att_date    = serializer.validated_data['date']
        att_status  = serializer.validated_data['status']
        remarks     = serializer.validated_data.get('remarks', '')

        try:
            employee = User.objects.get(id=employee_id)
        except User.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=status.HTTP_400_BAD_REQUEST)

        att, _ = Attendance.objects.update_or_create(
            employee=employee, date=att_date,
            defaults={'status': att_status, 'remarks': remarks}
        )
        return Response({'message': 'Attendance marked', 'attendance': AttendanceSerializer(att).data})


class AttendanceReportSummaryView(APIView):
    """Monthly attendance summary list — one row per month that has any attendance data"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.role or request.user.role.name not in ['HR', 'ADMIN']:
            return Response({'error': 'Only HR and Admin can view attendance reports'}, status=status.HTTP_403_FORBIDDEN)

        # Get distinct month/year combos that have attendance records
        from django.db.models import Count, Q
        summaries = (
            Attendance.objects
            .values('date__year', 'date__month')
            .annotate(total=Count('id'))
            .order_by('-date__year', '-date__month')
        )

        months = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']

        result = []
        for i, s in enumerate(summaries, 1):
            yr = s['date__year']
            mo = s['date__month']
            result.append({
                'index': i,
                'year': yr,
                'month': mo,
                'month_name': months[mo],
                'total_records': s['total'],
                'status': 'SUBMITTED',
                'submitted_date': f"01 {months[mo]} {yr}",
                'remark': '',
            })

        return Response(result)
