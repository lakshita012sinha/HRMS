from rest_framework import serializers
from .models import SalaryStructure, Salary
from accounts.models import User
from datetime import datetime


class SalaryStructureSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(source='employee.user_id', read_only=True)
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    gross_salary = serializers.SerializerMethodField()
    employee_deductions = serializers.SerializerMethodField()
    net_salary = serializers.SerializerMethodField()
    total_employer_cost = serializers.SerializerMethodField()
    ctc_breakdown = serializers.SerializerMethodField()
    
    class Meta:
        model = SalaryStructure
        fields = ['id', 'employee', 'employee_id', 'employee_name', 'ctc_monthly',
                  'basic_salary', 'hra', 'ca', 'cca', 'bonus', 'mobile',
                  'pf_employee', 'pf_employer', 'esi_employee', 'esi_employer',
                  'other_deductions', 'gross_salary', 'employee_deductions',
                  'net_salary', 'total_employer_cost', 'ctc_breakdown', 'is_active', 
                  'effective_from', 'created_at', 'updated_at']
        read_only_fields = ['basic_salary', 'hra', 'ca', 'cca', 'bonus',
                           'pf_employee', 'pf_employer', 'esi_employee', 'esi_employer',
                           'created_at', 'updated_at']
    
    def get_gross_salary(self, obj):
        return float(obj.calculate_gross_salary())
    
    def get_employee_deductions(self, obj):
        return float(obj.calculate_employee_deductions())
    
    def get_net_salary(self, obj):
        return float(obj.calculate_net_salary())
    
    def get_total_employer_cost(self, obj):
        return float(obj.calculate_total_employer_cost())
    
    def get_ctc_breakdown(self, obj):
        return obj.get_ctc_breakdown()
    
    def validate_employee(self, value):
        """Check if employee already has a salary structure"""
        if self.instance is None:  # Only for create
            if SalaryStructure.objects.filter(employee=value, is_active=True).exists():
                raise serializers.ValidationError(
                    "Active salary structure already exists for this employee"
                )
        return value
    
    def validate_ctc_monthly(self, value):
        """Validate CTC amount"""
        if value <= 0:
            raise serializers.ValidationError("CTC must be greater than 0")
        return value


class SalarySerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(source='employee.user_id', read_only=True)
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    month_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Salary
        fields = ['id', 'employee', 'employee_id', 'employee_name', 'month', 'month_name',
                  'year', 'ctc_monthly', 'basic_salary', 'hra', 'ca', 'cca', 'bonus', 'mobile',
                  'gross_salary', 'pf_employee', 'pf_employer', 'esi_employee', 'esi_employer',
                  'other_deductions', 'total_deductions', 'net_salary', 'status', 'paid_days',
                  'payment_date', 'remarks', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_month_name(self, obj):
        """Return month name"""
        months = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        return months[obj.month] if 1 <= obj.month <= 12 else ''
    
    def validate_month(self, value):
        """Validate month is between 1-12"""
        if not 1 <= value <= 12:
            raise serializers.ValidationError("Month must be between 1 and 12")
        return value
    
    def validate_year(self, value):
        """Validate year"""
        current_year = datetime.now().year
        if value < 2000 or value > current_year + 1:
            raise serializers.ValidationError(
                f"Year must be between 2000 and {current_year + 1}"
            )
        return value
    
    def validate(self, attrs):
        """Validate salary record"""
        employee = attrs.get('employee')
        month = attrs.get('month')
        year = attrs.get('year')
        
        # Check for duplicate salary record
        if self.instance is None:  # Only for create
            if Salary.objects.filter(employee=employee, month=month, year=year).exists():
                raise serializers.ValidationError({
                    "error": f"Salary record already exists for {month}/{year}"
                })
        
        return attrs


class CTCSalaryStructureSerializer(serializers.Serializer):
    """Serializer for creating CTC-based salary structure"""
    employee = serializers.IntegerField(required=True)
    ctc_monthly = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    mobile = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    other_deductions = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    effective_from = serializers.DateField(required=True)
    
    def validate_employee(self, value):
        """Check if employee exists"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Employee not found")
        return value
    
    def validate_ctc_monthly(self, value):
        """Validate CTC amount"""
        if value <= 0:
            raise serializers.ValidationError("CTC must be greater than 0")
        return value


class GenerateSalarySerializer(serializers.Serializer):
    """Serializer for generating salary"""
    employee = serializers.IntegerField(required=True)
    month = serializers.IntegerField(required=True, min_value=1, max_value=12)
    year = serializers.IntegerField(required=True, min_value=2000)
    
    def validate_employee(self, value):
        """Check if employee exists"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Employee not found")
        return value
    
    def validate(self, attrs):
        """Validate salary generation"""
        employee_id = attrs['employee']
        month = attrs['month']
        year = attrs['year']
        
        # Check if salary already exists
        if Salary.objects.filter(employee_id=employee_id, month=month, year=year).exists():
            raise serializers.ValidationError({
                "error": f"Salary already generated for {month}/{year}"
            })
        
        # Check if employee has salary structure
        try:
            SalaryStructure.objects.get(employee_id=employee_id, is_active=True)
        except SalaryStructure.DoesNotExist:
            raise serializers.ValidationError({
                "error": "No active salary structure found for this employee"
            })
        
        return attrs


class MarkSalaryPaidSerializer(serializers.Serializer):
    """Serializer for marking salary as paid"""
    payment_date = serializers.DateField(required=True)
    remarks = serializers.CharField(required=False, allow_blank=True)
