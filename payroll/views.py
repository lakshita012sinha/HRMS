from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from .models import SalaryStructure, Salary
from .serializers import (
    SalaryStructureSerializer, SalarySerializer,
    GenerateSalarySerializer, MarkSalaryPaidSerializer, CTCSalaryStructureSerializer
)
from accounts.models import User


class CreateCTCSalaryStructureView(APIView):
    """Create CTC-based salary structure"""
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        # Only HR/Admin can create salary structure
        if not request.user.role or request.user.role.name not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR and Admin can create salary structures'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CTCSalaryStructureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        employee_id = serializer.validated_data['employee']
        ctc_monthly = serializer.validated_data['ctc_monthly']
        mobile = serializer.validated_data.get('mobile', 0)
        other_deductions = serializer.validated_data.get('other_deductions', 0)
        effective_from = serializer.validated_data['effective_from']
        
        # Get employee
        employee = User.objects.get(id=employee_id)
        
        # Check if employee already has active salary structure
        if SalaryStructure.objects.filter(employee=employee, is_active=True).exists():
            return Response(
                {'error': 'Active salary structure already exists for this employee'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create salary structure (calculations will be done in model's save method)
        salary_structure = SalaryStructure.objects.create(
            employee=employee,
            ctc_monthly=ctc_monthly,
            mobile=mobile,
            other_deductions=other_deductions,
            effective_from=effective_from
        )
        
        return Response({
            'message': 'CTC-based salary structure created successfully',
            'salary_structure': SalaryStructureSerializer(salary_structure).data
        }, status=status.HTTP_201_CREATED)


# Salary Structure Management
class SalaryStructureListCreateView(generics.ListCreateAPIView):
    """List and create salary structures"""
    queryset = SalaryStructure.objects.filter(is_active=True)
    serializer_class = SalaryStructureSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = SalaryStructure.objects.filter(is_active=True)
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        elif user.role and user.role.name not in ['HR', 'ADMIN']:
            # Non-HR/Admin can only see their own salary structure
            queryset = queryset.filter(employee=user)
        
        return queryset.select_related('employee')
    
    def perform_create(self, serializer):
        # Only HR/Admin can create salary structure
        if not self.request.user.role or self.request.user.role.name not in ['HR', 'ADMIN']:
            raise permissions.PermissionDenied("Only HR and Admin can create salary structures")
        
        serializer.save()


class SalaryStructureDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete salary structure"""
    queryset = SalaryStructure.objects.all()
    serializer_class = SalaryStructureSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_update(self, serializer):
        # Only HR/Admin can update salary structure
        if not self.request.user.role or self.request.user.role.name not in ['HR', 'ADMIN']:
            raise permissions.PermissionDenied("Only HR and Admin can update salary structures")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        # Only HR/Admin can delete salary structure
        if not self.request.user.role or self.request.user.role.name not in ['HR', 'ADMIN']:
            raise permissions.PermissionDenied("Only HR and Admin can delete salary structures")
        
        # Soft delete
        instance.is_active = False
        instance.save()


class MySalaryStructureView(APIView):
    """Get current user's salary structure"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            salary_structure = SalaryStructure.objects.get(
                employee=request.user,
                is_active=True
            )
            serializer = SalaryStructureSerializer(salary_structure)
            return Response(serializer.data)
        except SalaryStructure.DoesNotExist:
            return Response(
                {'error': 'No salary structure found'},
                status=status.HTTP_404_NOT_FOUND
            )


# Salary Management
class SalaryListView(generics.ListAPIView):
    """List salary records"""
    serializer_class = SalarySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Salary.objects.all()
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        elif user.role and user.role.name not in ['HR', 'ADMIN']:
            # Non-HR/Admin can only see their own salary records
            queryset = queryset.filter(employee=user)
        
        # Filter by month and year
        month = self.request.query_params.get('month', None)
        year = self.request.query_params.get('year', None)
        if month:
            queryset = queryset.filter(month=month)
        if year:
            queryset = queryset.filter(year=year)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related('employee')


class SalaryDetailView(generics.RetrieveAPIView):
    """Retrieve salary record details"""
    queryset = Salary.objects.all()
    serializer_class = SalarySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Salary.objects.all()
        
        # Non-HR/Admin can only see their own salary records
        if user.role and user.role.name not in ['HR', 'ADMIN']:
            queryset = queryset.filter(employee=user)
        
        return queryset


class GenerateSalaryView(APIView):
    """Generate salary for an employee"""
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        # Only HR/Admin can generate salary
        if not request.user.role or request.user.role.name not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR and Admin can generate salary'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = GenerateSalarySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        employee_id = serializer.validated_data['employee']
        month = serializer.validated_data['month']
        year = serializer.validated_data['year']
        
        # Get employee
        employee = User.objects.get(id=employee_id)
        
        # Get salary structure
        try:
            salary_structure = SalaryStructure.objects.get(
                employee=employee,
                is_active=True
            )
        except SalaryStructure.DoesNotExist:
            return Response(
                {'error': 'No active salary structure found for this employee'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate salary components from salary structure
        ctc_monthly = salary_structure.ctc_monthly
        basic_salary = salary_structure.basic_salary
        hra = salary_structure.hra
        ca = salary_structure.ca
        cca = salary_structure.cca
        bonus = salary_structure.bonus
        mobile = salary_structure.mobile
        gross_salary = salary_structure.calculate_gross_salary()
        
        pf_employee = salary_structure.pf_employee
        pf_employer = salary_structure.pf_employer
        esi_employee = salary_structure.esi_employee
        esi_employer = salary_structure.esi_employer
        other_deductions = salary_structure.other_deductions
        total_deductions = salary_structure.calculate_employee_deductions()
        
        net_salary = gross_salary - total_deductions
        
        # Create salary record
        salary = Salary.objects.create(
            employee=employee,
            month=month,
            year=year,
            ctc_monthly=ctc_monthly,
            basic_salary=basic_salary,
            hra=hra,
            ca=ca,
            cca=cca,
            bonus=bonus,
            mobile=mobile,
            gross_salary=gross_salary,
            pf_employee=pf_employee,
            pf_employer=pf_employer,
            esi_employee=esi_employee,
            esi_employer=esi_employer,
            other_deductions=other_deductions,
            total_deductions=total_deductions,
            net_salary=net_salary,
            status='GENERATED'
        )
        
        return Response({
            'message': 'Salary generated successfully',
            'salary': SalarySerializer(salary).data
        }, status=status.HTTP_201_CREATED)


class MarkSalaryPaidView(APIView):
    """Mark salary as paid"""
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, pk):
        # Only HR/Admin can mark salary as paid
        if not request.user.role or request.user.role.name not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR and Admin can mark salary as paid'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            salary = Salary.objects.get(pk=pk)
        except Salary.DoesNotExist:
            return Response(
                {'error': 'Salary record not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if salary.status == 'PAID':
            return Response(
                {'error': 'Salary is already marked as paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if salary.status == 'CANCELLED':
            return Response(
                {'error': 'Cannot mark cancelled salary as paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = MarkSalaryPaidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        salary.status = 'PAID'
        salary.payment_date = serializer.validated_data['payment_date']
        salary.remarks = serializer.validated_data.get('remarks', '')
        salary.save()
        
        return Response({
            'message': 'Salary marked as paid successfully',
            'salary': SalarySerializer(salary).data
        }, status=status.HTTP_200_OK)


class CancelSalaryView(APIView):
    """Cancel salary record"""
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, pk):
        # Only HR/Admin can cancel salary
        if not request.user.role or request.user.role.name not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR and Admin can cancel salary'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            salary = Salary.objects.get(pk=pk)
        except Salary.DoesNotExist:
            return Response(
                {'error': 'Salary record not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if salary.status == 'PAID':
            return Response(
                {'error': 'Cannot cancel paid salary'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if salary.status == 'CANCELLED':
            return Response(
                {'error': 'Salary is already cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        salary.status = 'CANCELLED'
        salary.save()
        
        return Response({
            'message': 'Salary cancelled successfully',
            'salary': SalarySerializer(salary).data
        }, status=status.HTTP_200_OK)


class MySalaryView(APIView):
    """Get current user's salary records"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        year = request.query_params.get('year', datetime.now().year)
        month = request.query_params.get('month', None)
        
        queryset = Salary.objects.filter(employee=request.user, year=year)
        if month:
            queryset = queryset.filter(month=month)
        
        salaries = queryset.order_by('-year', '-month')
        serializer = SalarySerializer(salaries, many=True)
        return Response(serializer.data)


class GenerateMonthlyPayrollView(APIView):
    """
    Generate payroll for ALL employees for a given month based on attendance.
    Pay = (pay_days / total_days_in_month) * full_net_salary
    pay_days = present + sundays (as per attendance data)
    Skips employees with no salary structure or already-generated salary.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        if not request.user.role or request.user.role.name not in ['HR', 'ADMIN']:
            return Response({'error': 'Only HR and Admin can generate payroll'}, status=status.HTTP_403_FORBIDDEN)

        month = request.data.get('month')
        year  = request.data.get('year')
        if not month or not year:
            return Response({'error': 'month and year are required'}, status=status.HTTP_400_BAD_REQUEST)

        month = int(month)
        year  = int(year)

        import calendar as cal
        from attendance.models import Attendance, Holiday
        from datetime import date
        from decimal import Decimal

        days_in_month = cal.monthrange(year, month)[1]

        # Count sundays in the month
        sundays = sum(1 for d in range(1, days_in_month + 1) if date(year, month, d).weekday() == 6)

        # Holidays
        holidays = set(Holiday.objects.filter(date__year=year, date__month=month).values_list('date', flat=True))
        holiday_count = len(holidays)

        # All attendance records for this month
        att_qs = Attendance.objects.filter(date__year=year, date__month=month).select_related('employee')
        att_map = {}  # employee_id -> {present, half_day}
        for a in att_qs:
            emp_id = a.employee_id
            if emp_id not in att_map:
                att_map[emp_id] = {'present': 0, 'half_day': 0}
            if a.status == 'PRESENT':
                att_map[emp_id]['present'] += 1
            elif a.status == 'HALF_DAY':
                att_map[emp_id]['half_day'] += 1

        generated = []
        skipped   = []

        employees = User.objects.filter(is_active=True).exclude(role__name__in=['ADMIN'])
        for emp in employees:
            # Must have salary structure
            try:
                ss = SalaryStructure.objects.get(employee=emp, is_active=True)
            except SalaryStructure.DoesNotExist:
                skipped.append({'employee': emp.user_id, 'reason': 'No salary structure'})
                continue

            # Skip if already generated
            if Salary.objects.filter(employee=emp, month=month, year=year).exists():
                skipped.append({'employee': emp.user_id, 'reason': 'Salary already generated'})
                continue

            # Calculate pay days
            emp_att   = att_map.get(emp.id, {'present': 0, 'half_day': 0})
            present   = emp_att['present'] + emp_att['half_day'] * Decimal('0.5')
            pay_days  = present + sundays  # present days + all sundays

            # Cap at days_in_month
            pay_days = min(pay_days, days_in_month)

            # Prorate salary
            ratio = Decimal(str(pay_days)) / Decimal(str(days_in_month))

            gross        = ss.calculate_gross_salary() * ratio
            pf_employee  = ss.pf_employee  * ratio
            esi_employee = ss.esi_employee * ratio
            other_ded    = ss.other_deductions * ratio
            total_ded    = pf_employee + esi_employee + other_ded
            net_salary   = gross - total_ded

            # Round to 2dp
            def r(v): return v.quantize(Decimal('0.01'))

            sal = Salary.objects.create(
                employee=emp,
                month=month, year=year,
                ctc_monthly=ss.ctc_monthly,
                basic_salary=r(ss.basic_salary * ratio),
                hra=r(ss.hra * ratio),
                ca=r(ss.ca * ratio),
                cca=r(ss.cca * ratio),
                bonus=r(ss.bonus * ratio),
                mobile=r(ss.mobile * ratio),
                gross_salary=r(gross),
                pf_employee=r(pf_employee),
                pf_employer=r(ss.pf_employer * ratio),
                esi_employee=r(esi_employee),
                esi_employer=r(ss.esi_employer * ratio),
                other_deductions=r(other_ded),
                total_deductions=r(total_ded),
                net_salary=r(net_salary),
                status='GENERATED',
                paid_days=float(pay_days),
                remarks=f'Pay days: {pay_days}/{days_in_month} (Present:{present} + Sundays:{sundays})'
            )
            generated.append({
                'employee': emp.user_id,
                'name': f"{emp.first_name} {emp.last_name}".strip(),
                'pay_days': float(pay_days),
                'net_salary': float(sal.net_salary),
            })

        return Response({
            'message': f'Payroll generated for {len(generated)} employees.',
            'month': month, 'year': year,
            'generated': generated,
            'skipped': skipped,
        }, status=status.HTTP_201_CREATED)
