from rest_framework import serializers
from .models import (
    Shift, EmployeeShiftAssignment, Holiday, Attendance,
    AttendanceLog, GeoTracking, AttendanceRegularization
)
from accounts.models import User
from django.utils import timezone


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'


class EmployeeShiftAssignmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.user_id', read_only=True)
    shift_name = serializers.CharField(source='shift.shift_name', read_only=True)
    
    class Meta:
        model = EmployeeShiftAssignment
        fields = ['id', 'employee', 'employee_id', 'employee_name', 'shift', 
                  'shift_name', 'start_date', 'end_date', 'is_active', 'created_at']


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = '__all__'


class GeoTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoTracking
        fields = ['latitude', 'longitude', 'address', 'accuracy']


class AttendanceLogSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.user_id', read_only=True)
    geo_tracking = GeoTrackingSerializer(read_only=True)
    
    class Meta:
        model = AttendanceLog
        fields = ['id', 'employee', 'employee_id', 'employee_name', 'attendance',
                  'timestamp', 'log_type', 'location', 'device', 'ip_address',
                  'geo_tracking', 'created_at']
        read_only_fields = ['employee', 'created_at']


class CheckInSerializer(serializers.Serializer):
    """Serializer for check-in with GPS"""
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    address = serializers.CharField(required=False, allow_blank=True)
    accuracy = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    device = serializers.CharField(required=False, allow_blank=True)


class CheckOutSerializer(serializers.Serializer):
    """Serializer for check-out with GPS"""
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=True)
    address = serializers.CharField(required=False, allow_blank=True)
    accuracy = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    device = serializers.CharField(required=False, allow_blank=True)


class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.user_id', read_only=True)
    logs = AttendanceLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = Attendance
        fields = ['id', 'employee', 'employee_id', 'employee_name', 'date',
                  'check_in_time', 'check_out_time', 'total_hours', 'status',
                  'location', 'remarks', 'logs', 'created_at', 'updated_at']
        read_only_fields = ['total_hours', 'created_at', 'updated_at']


class AttendanceRegularizationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.user_id', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    attendance_date = serializers.DateField(source='attendance.date', read_only=True)
    
    class Meta:
        model = AttendanceRegularization
        fields = ['id', 'employee', 'employee_id', 'employee_name', 'attendance',
                  'attendance_date', 'requested_check_in', 'requested_check_out',
                  'reason', 'status', 'approved_by', 'approved_by_name',
                  'approved_at', 'rejection_reason', 'created_at', 'updated_at']
        read_only_fields = ['employee', 'status', 'approved_by', 'approved_at', 'created_at', 'updated_at']


class ApproveRegularizationSerializer(serializers.Serializer):
    """Serializer for approving/rejecting regularization"""
    status = serializers.ChoiceField(choices=['APPROVED', 'REJECTED'], required=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)


class BulkAttendanceSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField(required=True)
    date        = serializers.DateField(required=True)
    status      = serializers.ChoiceField(choices=['PRESENT', 'ABSENT', 'HALF_DAY', 'LEAVE', 'HOLIDAY', 'WEEKEND'])
    remarks     = serializers.CharField(required=False, allow_blank=True)
