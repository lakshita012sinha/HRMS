from django.contrib import admin
from .models import (
    Shift, EmployeeShiftAssignment, Holiday, Attendance,
    AttendanceLog, GeoTracking, AttendanceRegularization
)


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['shift_name', 'start_time', 'end_time', 'full_day_hours', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['shift_name']


@admin.register(EmployeeShiftAssignment)
class EmployeeShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'shift', 'start_date', 'end_date', 'is_active']
    list_filter = ['shift', 'is_active', 'start_date']
    search_fields = ['employee__user_id', 'employee__first_name', 'employee__last_name']
    date_hierarchy = 'start_date'


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ['holiday_name', 'date', 'is_optional']
    list_filter = ['is_optional', 'date']
    search_fields = ['holiday_name']
    date_hierarchy = 'date'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'check_in_time', 'check_out_time', 'total_hours', 'status']
    list_filter = ['status', 'date']
    search_fields = ['employee__user_id', 'employee__first_name', 'employee__last_name']
    date_hierarchy = 'date'
    readonly_fields = ['total_hours']


@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ['employee', 'log_type', 'timestamp', 'location', 'device']
    list_filter = ['log_type', 'timestamp']
    search_fields = ['employee__user_id', 'employee__first_name', 'employee__last_name']
    date_hierarchy = 'timestamp'


@admin.register(GeoTracking)
class GeoTrackingAdmin(admin.ModelAdmin):
    list_display = ['attendance_log', 'latitude', 'longitude', 'accuracy', 'created_at']
    list_filter = ['created_at']
    search_fields = ['attendance_log__employee__user_id', 'address']
    readonly_fields = ['latitude', 'longitude', 'address', 'accuracy']


@admin.register(AttendanceRegularization)
class AttendanceRegularizationAdmin(admin.ModelAdmin):
    list_display = ['employee', 'attendance', 'status', 'requested_check_in', 'approved_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['employee__user_id', 'employee__first_name', 'employee__last_name']
    date_hierarchy = 'created_at'
    readonly_fields = ['employee', 'created_at']
