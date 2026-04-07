from rest_framework import serializers
from .models import LeaveType, LeaveBalance, LeaveRequest, LeavePolicy
from accounts.models import User
from datetime import datetime


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'


class LeaveBalanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.user_id', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    
    class Meta:
        model = LeaveBalance
        fields = ['id', 'employee', 'employee_id', 'employee_name', 'leave_type',
                  'leave_type_name', 'year', 'total_allocated', 'used', 'available',
                  'created_at', 'updated_at']
        read_only_fields = ['available', 'created_at', 'updated_at']


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.user_id', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = LeaveRequest
        fields = ['id', 'employee', 'employee_id', 'employee_name', 'leave_type',
                  'leave_type_name', 'start_date', 'end_date', 'total_days', 'reason',
                  'status', 'approved_by', 'approved_by_name', 'approved_at',
                  'rejection_reason', 'created_at', 'updated_at']
        read_only_fields = ['employee', 'total_days', 'status', 'approved_by', 
                           'approved_at', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Validate leave request"""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        # Check if end_date is after start_date
        if end_date < start_date:
            raise serializers.ValidationError({
                "end_date": "End date must be after start date"
            })
        
        # Check if dates are in the past
        if start_date < datetime.now().date():
            raise serializers.ValidationError({
                "start_date": "Cannot apply leave for past dates"
            })
        
        return attrs


class ApplyLeaveSerializer(serializers.Serializer):
    """Serializer for applying leave"""
    employee_id = serializers.IntegerField(required=False, allow_null=True)
    leave_type = serializers.IntegerField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    reason = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['end_date'] < attrs['start_date']:
            raise serializers.ValidationError({"end_date": "End date must be after start date"})
        return attrs


class ApproveLeaveSerializer(serializers.Serializer):
    """Serializer for approving/rejecting leave"""
    status = serializers.ChoiceField(choices=['APPROVED', 'REJECTED'], required=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)


class LeavePolicySerializer(serializers.ModelSerializer):
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    
    class Meta:
        model = LeavePolicy
        fields = '__all__'
