from django.contrib import admin
from .models import LeaveType, LeaveBalance, LeaveRequest, LeavePolicy


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'max_days_per_year', 'is_paid', 'requires_approval', 'is_active']
    list_filter = ['is_paid', 'requires_approval', 'is_active']
    search_fields = ['name', 'code']


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'year', 'total_allocated', 'used', 'available']
    list_filter = ['year', 'leave_type']
    search_fields = ['employee__user_id', 'employee__first_name', 'employee__last_name']
    readonly_fields = ['available', 'created_at', 'updated_at']


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'total_days', 'status', 'approved_by']
    list_filter = ['status', 'leave_type', 'start_date']
    search_fields = ['employee__user_id', 'employee__first_name', 'employee__last_name', 'reason']
    readonly_fields = ['total_days', 'approved_at', 'created_at', 'updated_at']
    date_hierarchy = 'start_date'


@admin.register(LeavePolicy)
class LeavePolicyAdmin(admin.ModelAdmin):
    list_display = ['leave_type', 'min_notice_days', 'max_consecutive_days', 'can_carry_forward', 'is_active']
    list_filter = ['can_carry_forward', 'is_active']
    search_fields = ['leave_type__name']
