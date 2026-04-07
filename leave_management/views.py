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
            # Employees can only see their own requests
            queryset = queryset.filter(employee=user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
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

        # Balance check — HR/Admin bypass if no balance record exists (auto-create)
        try:
            balance = LeaveBalance.objects.get(employee=employee, leave_type=leave_type, year=year)
            if not is_hr and balance.available < total_days:
                return Response(
                    {'error': f'Insufficient leave balance. Available: {balance.available} days'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except LeaveBalance.DoesNotExist:
            if is_hr:
                # Auto-create balance for HR-applied leaves
                balance = LeaveBalance.objects.create(
                    employee=employee,
                    leave_type=leave_type,
                    year=year,
                    total_allocated=leave_type.max_days_per_year,
                    used=0,
                    available=leave_type.max_days_per_year
                )
            else:
                return Response(
                    {'error': 'No leave balance found for this leave type and year'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Check overlapping
        overlapping = LeaveRequest.objects.filter(
            employee=employee, status__in=['PENDING', 'APPROVED']
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
            status='PENDING'
        )

        return Response({
            'message': 'Leave request submitted successfully',
            'leave_request': LeaveRequestSerializer(leave_request).data
        }, status=status.HTTP_201_CREATED)


class ApproveLeaveView(APIView):
    """Approve or reject leave request"""
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, pk):
        # Only HR/Admin/Manager can approve
        if not request.user.role or request.user.role.name not in ['HR', 'ADMIN', 'MANAGER']:
            return Response(
                {'error': 'Only HR, Admin, and Managers can approve leave requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            leave_request = LeaveRequest.objects.get(pk=pk)
        except LeaveRequest.DoesNotExist:
            return Response(
                {'error': 'Leave request not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if leave_request.status != 'PENDING':
            return Response(
                {'error': f'Leave request is already {leave_request.status.lower()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ApproveLeaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        leave_request.status = serializer.validated_data['status']
        leave_request.approved_by = request.user
        leave_request.approved_at = timezone.now()
        
        if serializer.validated_data['status'] == 'APPROVED':
            # Update leave balance
            year = leave_request.start_date.year
            balance = LeaveBalance.objects.get(
                employee=leave_request.employee,
                leave_type=leave_request.leave_type,
                year=year
            )
            balance.used += leave_request.total_days
            balance.calculate_available()
            balance.save()
        else:
            leave_request.rejection_reason = serializer.validated_data.get('rejection_reason', '')
        
        leave_request.save()
        
        return Response({
            'message': f'Leave request {serializer.validated_data["status"].lower()}',
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
