from django.contrib import admin
from .models import SalaryStructure, Salary


@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ['employee', 'ctc_monthly', 'basic_salary', 'hra', 'ca', 'cca', 
                    'bonus', 'mobile', 'pf_employee', 'pf_employer', 'is_active', 'effective_from']
    list_filter = ['is_active', 'effective_from']
    search_fields = ['employee__user_id', 'employee__first_name', 'employee__last_name']
    readonly_fields = ['basic_salary', 'hra', 'ca', 'cca', 'bonus', 
                       'pf_employee', 'pf_employer', 'esi_employee', 'esi_employer',
                       'created_at', 'updated_at']
    date_hierarchy = 'effective_from'
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee', 'is_active', 'effective_from')
        }),
        ('CTC Configuration', {
            'fields': ('ctc_monthly',)
        }),
        ('Auto-Calculated Earnings', {
            'fields': ('basic_salary', 'hra', 'ca', 'cca', 'bonus'),
            'classes': ('collapse',)
        }),
        ('Mobile & Other Deductions', {
            'fields': ('mobile', 'other_deductions')
        }),
        ('Auto-Calculated PF', {
            'fields': ('pf_employee', 'pf_employer'),
            'classes': ('collapse',)
        }),
        ('Auto-Calculated ESI', {
            'fields': ('esi_employee', 'esi_employer'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Salary)
class SalaryAdmin(admin.ModelAdmin):
    list_display = ['employee', 'month', 'year', 'ctc_monthly', 'basic_salary', 
                    'gross_salary', 'total_deductions', 'net_salary', 'status', 'payment_date']
    list_filter = ['status', 'year', 'month']
    search_fields = ['employee__user_id', 'employee__first_name', 'employee__last_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Employee & Period', {
            'fields': ('employee', 'month', 'year')
        }),
        ('CTC & Basic', {
            'fields': ('ctc_monthly', 'basic_salary')
        }),
        ('Salary Components', {
            'fields': ('hra', 'ca', 'cca', 'bonus', 'mobile', 'gross_salary')
        }),
        ('PF Breakdown', {
            'fields': ('pf_employee', 'pf_employer')
        }),
        ('ESI Breakdown', {
            'fields': ('esi_employee', 'esi_employer')
        }),
        ('Deductions & Net', {
            'fields': ('other_deductions', 'total_deductions', 'net_salary')
        }),
        ('Payment Information', {
            'fields': ('status', 'payment_date', 'remarks')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
