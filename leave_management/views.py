from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from datetime import datetime
from .models import LeaveType, LeaveBalance, LeaveRequest, LeavePolicy
from .serializers import (
    LeaveTypeSerializer, LeaveBalanceSerializer, LeaveRequestSerializer,
    ApplyLeaveSerializer, ApproveLeaveSerializer, LeavePolicySerializer
)
from accounts.models import User
from accounts.models_extended import EmployeeProfile, EmploymentDetails


# Leave Type Management
class LeaveTypeListCreateView(generics.ListCreateAPIView):
    """List and create leave types"""
    queryset = LeaveType.objects.filter(is_active=True)
    serializer_class = LeaveTypeSerializer
    permission_classes = [permissions.IsAuthenticated]


class LeaveTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete leave type"""
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    permission_classes = [permissions.IsAuthenticated]


# Leave Balance Management
class LeaveBalanceListView(generics.ListAPIView):
    """List leave balances"""
    serializer_class = LeaveBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = LeaveBalance.objects.all()
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        elif user.role and user.role.name not in ['HR', 'ADMIN']:
            # Non-HR/Admin can only see their own balance
            queryset = queryset.filter(employee=user)
        
        # Filter by year
        year = self.request.query_params.get('year', datetime.now().year)
        queryset = queryset.filter(year=year)
        
        return queryset


class MyLeaveBalanceView(APIView):
    """Get current user's leave balance"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        year = request.query_params.get('year', datetime.now().year)
        balances = LeaveBalance.objects.filter(employee=request.user, year=year)
        serializer = LeaveBalanceSerializer(balances, many=True)
        return Response(serializer.data)


class LeaveBalanceCreateView(generics.CreateAPIView):
    """Create leave balance (HR/Admin only)"""
    queryset = LeaveBalance.objects.all()
    serializer_class = LeaveBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # Only HR/Admin can create leave balance
        if not self.request.user.role or self.request.user.role.name not in ['HR', 'ADMIN']:
            raise permissions.PermissionDenied("Only HR and Admin can allocate leave balance")
        
        balance = serializer.save()
        balance.calculate_available()
        balance.save()


# Leave Request Management
class LeaveRequestListView(generics.ListAPIView):
    """List leave requests"""
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = LeaveRequest.objects.all()
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        elif user.role and user.role.name not in ['HR', 'ADMIN', 'MANAGER']:
            # Employees can only see their own requests or requests of employees they report to/manage
            queryset = queryset.filter(
                Q(employee=user) |
                Q(employee__reporting_manager=user) |
                Q(employee__employee_profile__employment_details__reporting_officer=user)
            )
        
        # Filter by reporting manager
        reporting_manager_id = self.request.query_params.get('reporting_manager', None)
        if reporting_manager_id:
            queryset = queryset.filter(
                Q(employee__reporting_manager_id=reporting_manager_id) |
                Q(employee__employee_profile__employment_details__reporting_officer_id=reporting_manager_id)
            )
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            if status_filter == 'PENDING':
                queryset = queryset.filter(status__in=['PENDING', 'PENDING_MANAGER', 'PENDING_HR'])
            else:
                queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        
        return queryset.order_by('-created_at')


class LeaveRequestDetailView(generics.RetrieveAPIView):
    """Retrieve leave request details"""
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]


class ApplyLeaveView(APIView):
    """Apply for leave — self or on behalf of employee (HR/Admin only)"""
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = ApplyLeaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # HR/Admin can pass employee_id to apply on behalf of someone
        employee_id = serializer.validated_data.get('employee_id')
        if employee_id:
            if not request.user.role or request.user.role.name not in ['HR', 'ADMIN']:
                return Response(
                    {'error': 'Only HR and Admin can apply leave on behalf of employees'},
                    status=status.HTTP_403_FORBIDDEN
                )
            try:
                employee = User.objects.get(id=employee_id)
            except User.DoesNotExist:
                return Response({'error': 'Employee not found'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            employee = request.user

        leave_type_id = serializer.validated_data['leave_type']
        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']
        reason = serializer.validated_data['reason']

        try:
            leave_type = LeaveType.objects.get(id=leave_type_id, is_active=True)
        except LeaveType.DoesNotExist:
            return Response({'error': 'Invalid leave type'}, status=status.HTTP_400_BAD_REQUEST)

        total_days = (end_date - start_date).days + 1
        year = start_date.year
        is_hr = request.user.role and request.user.role.name in ['HR', 'ADMIN']

        # Balance check — Auto-create balance record if it doesn't exist
        try:
            balance = LeaveBalance.objects.get(employee=employee, leave_type=leave_type, year=year)
        except LeaveBalance.DoesNotExist:
            balance = LeaveBalance.objects.create(
                employee=employee,
                leave_type=leave_type,
                year=year,
                total_allocated=leave_type.max_days_per_year,
                used=0,
                available=leave_type.max_days_per_year
            )

        if not is_hr and balance.available < total_days:
            return Response(
                {'error': f'Insufficient leave balance. Available: {balance.available} days'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check overlapping
        overlapping = LeaveRequest.objects.filter(
            employee=employee, status__in=['PENDING', 'PENDING_MANAGER', 'PENDING_HR', 'APPROVED']
        ).filter(Q(start_date__lte=end_date) & Q(end_date__gte=start_date))

        if overlapping.exists():
            return Response({'error': 'Overlapping leave request exists'}, status=status.HTTP_400_BAD_REQUEST)

        leave_request = LeaveRequest.objects.create(
            employee=employee,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            reason=reason,
            status='PENDING_MANAGER'
        )

        # Notify reporting manager(s) and HR immediately
        try:
            from .models import LeaveNotification
            
            # 1. Notify Reporting Manager(s)
            manager_recipients = set()
            if employee.reporting_manager:
                manager_recipients.add(employee.reporting_manager)
            try:
                from accounts.models_extended import EmploymentDetails
                emp_details = EmploymentDetails.objects.get(employee__user=employee)
                if emp_details.reporting_officer:
                    manager_recipients.add(emp_details.reporting_officer)
            except Exception:
                pass
                
            for m in manager_recipients:
                LeaveNotification.objects.create(
                    recipient=m,
                    leave_request=leave_request,
                    message=f"{employee.get_full_name()} ({employee.user_id}) has applied for {leave_type.name} from {start_date} to {end_date}."
                )
                
            # 2. Notify HR users
            hr_users = User.objects.filter(role__name__in=['HR', 'ADMIN'])
            for hr in hr_users:
                LeaveNotification.objects.create(
                    recipient=hr,
                    leave_request=leave_request,
                    message=f"New leave request from {employee.get_full_name()} ({employee.user_id}) for {leave_type.name} from {start_date} to {end_date} (Pending Manager Approval)."
                )
        except Exception as e:
            pass  # Notification failure shouldn't block leave creation

        return Response({
            'message': 'Leave request submitted successfully',
            'leave_request': LeaveRequestSerializer(leave_request).data
        }, status=status.HTTP_201_CREATED)


def update_attendance_for_leave(leave_request):
    """Automatically create or update Attendance records to status='LEAVE' for leave dates"""
    from attendance.models import Attendance
    from datetime import timedelta
    
    curr_date = leave_request.start_date
    end_date = leave_request.end_date
    while curr_date <= end_date:
        att, created = Attendance.objects.get_or_create(
            employee=leave_request.employee,
            date=curr_date,
            defaults={'status': 'LEAVE'}
        )
        if not created:
            att.status = 'LEAVE'
            att.save()
        curr_date += timedelta(days=1)


class ApproveLeaveView(APIView):
    """Approve or reject leave request"""
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, pk):
        try:
            leave_request = LeaveRequest.objects.get(pk=pk)
        except LeaveRequest.DoesNotExist:
            return Response(
                {'error': 'Leave request not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        user = request.user
        role_name = user.role.name if user.role else 'EMPLOYEE'
        
        # Determine if request.user is the reporting manager
        is_reporting_manager = False
        if leave_request.employee.reporting_manager == user:
            is_reporting_manager = True
        else:
            try:
                from accounts.models_extended import EmploymentDetails
                emp_details = EmploymentDetails.objects.get(employee__user=leave_request.employee)
                if emp_details.reporting_officer == user:
                    is_reporting_manager = True
            except Exception:
                pass

        # Only HR/Admin/Manager or the specific reporting manager/officer can approve
        is_authorized = role_name in ['HR', 'ADMIN', 'MANAGER'] or is_reporting_manager
        if not is_authorized:
            return Response(
                {'error': 'Only HR, Admin, and Managers can approve leave requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if leave_request.status in ['APPROVED', 'REJECTED', 'CANCELLED']:
            return Response(
                {'error': f'Leave request is already {leave_request.status.lower()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ApproveLeaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action_status = serializer.validated_data['status']  # 'APPROVED' or 'REJECTED'
        rejection_reason = serializer.validated_data.get('rejection_reason', '')
        remarks = serializer.validated_data.get('remarks', '')
                
        is_hr_or_admin = role_name in ['HR', 'ADMIN']
        from .models import LeaveNotification, LeaveApprovalHistory, LeaveBalance
        from django.conf import settings
        from datetime import timedelta
        
        action_name = ''
        notify_msg = ''
        
        if leave_request.status == 'PENDING_MANAGER':
            if is_reporting_manager:
                if action_status == 'APPROVED':
                    leave_request.status = 'PENDING_HR'
                    action_name = 'Manager Approved'
                    notify_msg = f"Manager {user.get_full_name()} approved. Pending HR Final Approval."
                    
                    # Notify HR
                    hr_users = User.objects.filter(role__name__in=['HR', 'ADMIN'])
                    for hr in hr_users:
                        LeaveNotification.objects.create(
                            recipient=hr,
                            leave_request=leave_request,
                            message=f"Manager approved leave for {leave_request.employee.get_full_name()} ({leave_request.employee.user_id}). Pending HR Final Approval."
                        )
                else:
                    leave_request.status = 'REJECTED'
                    leave_request.rejection_reason = rejection_reason
                    action_name = 'Manager Rejected'
                    notify_msg = f"Manager {user.get_full_name()} rejected the leave request."
                    
                    # Notify Employee
                    LeaveNotification.objects.create(
                        recipient=leave_request.employee,
                        leave_request=leave_request,
                        message=f"Your leave request has been rejected by Manager {user.get_full_name()}. Reason: {rejection_reason}"
                    )
            elif is_hr_or_admin:
                # HR Override
                time_diff = timezone.now() - leave_request.created_at
                escalation_hours = getattr(settings, 'LEAVE_ESCALATION_HOURS', 48)
                if time_diff.total_seconds() >= escalation_hours * 3600:
                    if action_status == 'APPROVED':
                        leave_request.status = 'APPROVED'
                        leave_request.approved_by = user
                        leave_request.approved_at = timezone.now()
                        action_name = 'HR Override Approved'
                        notify_msg = f"HR {user.get_full_name()} override-approved the leave request."
                        
                        # Update balance
                        year = leave_request.start_date.year
                        balance = LeaveBalance.objects.get(
                            employee=leave_request.employee,
                            leave_type=leave_request.leave_type,
                            year=year
                        )
                        balance.used += leave_request.total_days
                        balance.calculate_available()
                        balance.save()
                        
                        # Update attendance
                        update_attendance_for_leave(leave_request)
                        
                        # Notify Employee
                        LeaveNotification.objects.create(
                            recipient=leave_request.employee,
                            leave_request=leave_request,
                            message=f"Your leave request has been override-approved by HR. Status is now Approved."
                        )
                    else:
                        leave_request.status = 'REJECTED'
                        leave_request.rejection_reason = rejection_reason
                        action_name = 'HR Override Rejected'
                        notify_msg = f"HR {user.get_full_name()} override-rejected the leave request."
                        
                        # Notify Employee
                        LeaveNotification.objects.create(
                            recipient=leave_request.employee,
                            leave_request=leave_request,
                            message=f"Your leave request has been override-rejected by HR. Reason: {rejection_reason}"
                        )
                else:
                    return Response(
                        {'error': f'Cannot override yet. Manager has {escalation_hours} hours to act before HR override is active.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {'error': 'Only the reporting manager can act on this request, or HR can override after 48 hours.'},
                    status=status.HTTP_403_FORBIDDEN
                )
                
        elif leave_request.status == 'PENDING_HR':
            if is_hr_or_admin:
                if action_status == 'APPROVED':
                    leave_request.status = 'APPROVED'
                    leave_request.approved_by = user
                    leave_request.approved_at = timezone.now()
                    action_name = 'HR Approved'
                    notify_msg = f"HR {user.get_full_name()} finally approved the leave request."
                    
                    # Update balance
                    year = leave_request.start_date.year
                    balance = LeaveBalance.objects.get(
                        employee=leave_request.employee,
                        leave_type=leave_request.leave_type,
                        year=year
                    )
                    balance.used += leave_request.total_days
                    balance.calculate_available()
                    balance.save()
                    
                    # Update attendance
                    update_attendance_for_leave(leave_request)
                    
                    # Notify Employee
                    LeaveNotification.objects.create(
                        recipient=leave_request.employee,
                        leave_request=leave_request,
                        message=f"Your leave request has been finally approved by HR."
                    )
                else:
                    leave_request.status = 'REJECTED'
                    leave_request.rejection_reason = rejection_reason
                    action_name = 'HR Rejected'
                    notify_msg = f"HR {user.get_full_name()} rejected the leave request."
                    
                    # Notify Employee
                    LeaveNotification.objects.create(
                        recipient=leave_request.employee,
                        leave_request=leave_request,
                        message=f"Your leave request has been rejected by HR. Reason: {rejection_reason}"
                    )
            else:
                return Response(
                    {'error': 'Only HR or Admin can perform final approval/rejection.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            # Fallback for legacy PENDING requests
            if is_hr_or_admin or is_reporting_manager:
                if action_status == 'APPROVED':
                    if is_hr_or_admin:
                        leave_request.status = 'APPROVED'
                        leave_request.approved_by = user
                        leave_request.approved_at = timezone.now()
                        action_name = 'HR Approved'
                        notify_msg = f"Leave request approved by HR."
                        
                        # Update balance
                        year = leave_request.start_date.year
                        balance = LeaveBalance.objects.get(
                            employee=leave_request.employee,
                            leave_type=leave_request.leave_type,
                            year=year
                        )
                        balance.used += leave_request.total_days
                        balance.calculate_available()
                        balance.save()
                        
                        # Update attendance
                        update_attendance_for_leave(leave_request)
                    else:
                        leave_request.status = 'PENDING_HR'
                        action_name = 'Manager Approved'
                        notify_msg = f"Manager approved. Pending HR Final Approval."
                else:
                    leave_request.status = 'REJECTED'
                    leave_request.rejection_reason = rejection_reason
                    action_name = 'Rejected'
                    notify_msg = f"Leave request rejected."
                    
                    # Notify Employee
                    LeaveNotification.objects.create(
                        recipient=leave_request.employee,
                        leave_request=leave_request,
                        message=f"Your leave request has been rejected. Reason: {rejection_reason}"
                    )
            else:
                return Response(
                    {'error': 'No permissions to act on this leave request.'},
                    status=status.HTTP_403_FORBIDDEN
                )
                
        leave_request.save()
        
        # Record approval history
        LeaveApprovalHistory.objects.create(
            leave_request=leave_request,
            action_by=user,
            role=role_name or 'UNKNOWN',
            action=action_name,
            remarks=remarks or rejection_reason or notify_msg
        )
        
        return Response({
            'message': notify_msg,
            'leave_request': LeaveRequestSerializer(leave_request).data
        }, status=status.HTTP_200_OK)


class CancelLeaveView(APIView):
    """Cancel leave request"""
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, pk):
        try:
            leave_request = LeaveRequest.objects.get(pk=pk, employee=request.user)
        except LeaveRequest.DoesNotExist:
            return Response(
                {'error': 'Leave request not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if leave_request.status == 'CANCELLED':
            return Response(
                {'error': 'Leave request is already cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If approved, restore leave balance
        if leave_request.status == 'APPROVED':
            year = leave_request.start_date.year
            balance = LeaveBalance.objects.get(
                employee=leave_request.employee,
                leave_type=leave_request.leave_type,
                year=year
            )
            balance.used -= leave_request.total_days
            balance.calculate_available()
            balance.save()
        
        leave_request.status = 'CANCELLED'
        leave_request.save()
        
        return Response({
            'message': 'Leave request cancelled successfully',
            'leave_request': LeaveRequestSerializer(leave_request).data
        }, status=status.HTTP_200_OK)


# Leave Policy Management
class LeavePolicyListCreateView(generics.ListCreateAPIView):
    """List and create leave policies"""
    queryset = LeavePolicy.objects.filter(is_active=True)
    serializer_class = LeavePolicySerializer
    permission_classes = [permissions.IsAuthenticated]


class LeavePolicyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete leave policy"""
    queryset = LeavePolicy.objects.all()
    serializer_class = LeavePolicySerializer
    permission_classes = [permissions.IsAuthenticated]


class NotificationListView(APIView):
    """Get notifications for the logged-in user"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .models import LeaveNotification
        notifications = LeaveNotification.objects.filter(
            recipient=request.user
        ).select_related('leave_request__employee', 'leave_request__leave_type').order_by('-created_at')[:20]

        data = [{
            'id': n.id,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%d %b %Y %H:%M'),
            'leave_request_id': n.leave_request_id,
        } for n in notifications]

        unread_count = LeaveNotification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({'notifications': data, 'unread_count': unread_count})

    def patch(self, request):
        """Mark all as read"""
        from .models import LeaveNotification
        LeaveNotification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'All notifications marked as read'})
