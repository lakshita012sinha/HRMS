from rest_framework import serializers
from .models_extended import (
    Branch, Department, Designation, EmployeeProfile,
    EmergencyContact, EmploymentDetails, BankDetails, EmployeeDocument, Promotion, Increment
)
from .models import User


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        fields = '__all__'


class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ['relationship_name', 'relationship_type', 'parent_mobile', 'another_mobile']


class EmploymentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmploymentDetails
        fields = ['branch', 'department', 'designation', 'grade', 'employment_type',
                  'reporting_officer', 'deputed_project', 'effective_date']


class BankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDetails
        fields = ['bank_name', 'bank_branch', 'account_number', 'ifsc_code', 'is_salary_account']


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDocument
        fields = ['document_type', 'document_file']


class EmployeeProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeProfile
        fields = [
            'father_name', 'mother_name', 'date_of_birth', 'gender', 'date_of_joining',
            'height_cm', 'weight_kg', 'blood_group', 'marital_status',
            'official_email', 'contact_number', 'another_contact_number',
            'pan_number', 'uid_number', 'una_number', 'esic_number', 'pf_number',
            'qualification', 'present_address', 'present_city', 'present_state',
            'present_pincode', 'same_as_present_address', 'permanent_address',
            'permanent_city', 'permanent_state', 'permanent_pincode'
        ]


class PromotionSerializer(serializers.ModelSerializer):
    employee_code = serializers.CharField(required=False, write_only=True)
    promoted_designation_name = serializers.CharField(required=False, write_only=True)
    designation_name = serializers.CharField(source='promoted_designation.name', read_only=True)

    class Meta:
        model = Promotion
        fields = [
            'id', 'employee', 'employee_code', 'promoted_date', 'promoted_designation', 
            'promoted_designation_name', 'designation_name', 'pay_level', 'basic_pay', 
            'effective_date_from', 'approved_by', 'remark', 'document', 'created_at'
        ]
        extra_kwargs = {
            'employee': {'required': False, 'allow_null': True},
            'promoted_designation': {'required': False, 'allow_null': True}
        }

    def create(self, validated_data):
        employee_code = validated_data.pop('employee_code', None)
        employee = validated_data.pop('employee', None)
        
        if not employee and employee_code:
            employee = EmployeeProfile.objects.filter(user__user_id=employee_code).first()
            if not employee:
                raise serializers.ValidationError({"employee": f"Employee with code {employee_code} not found."})

        desig_val = validated_data.pop('promoted_designation_name', None)
        promoted_designation = validated_data.pop('promoted_designation', None)
        
        if not promoted_designation and desig_val:
            desig_val_str = str(desig_val).strip()
            if desig_val_str:
                if desig_val_str.isdigit():
                    promoted_designation = Designation.objects.filter(id=int(desig_val_str)).first()
                if not promoted_designation:
                    promoted_designation, _ = Designation.objects.get_or_create(
                        name=desig_val_str,
                        defaults={'code': desig_val_str[:20].upper()}
                    )

        validated_data['employee'] = employee
        validated_data['promoted_designation'] = promoted_designation
        
        return super().create(validated_data)


class IncrementSerializer(serializers.ModelSerializer):
    employee_code = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = Increment
        fields = [
            'id', 'employee', 'employee_code', 'increment_date', 'increment_type', 
            'pay_level', 'previous_basic_pay', 'increment_amount', 'new_basic_pay', 
            'effective_date_from', 'approved_by', 'remark', 'document', 'created_at'
        ]
        extra_kwargs = {
            'employee': {'required': False, 'allow_null': True}
        }

    def create(self, validated_data):
        employee_code = validated_data.pop('employee_code', None)
        employee = validated_data.pop('employee', None)
        
        if not employee and employee_code:
            employee = EmployeeProfile.objects.filter(user__user_id=employee_code).first()
            if not employee:
                raise serializers.ValidationError({"employee": f"Employee with code {employee_code} not found."})

        validated_data['employee'] = employee
        return super().create(validated_data)


