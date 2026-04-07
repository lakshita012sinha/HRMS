from rest_framework import serializers
from .models_extended import (
    Branch, Department, Designation, EmployeeProfile,
    EmergencyContact, EmploymentDetails, BankDetails, EmployeeDocument
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
