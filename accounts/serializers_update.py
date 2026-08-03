from rest_framework import serializers
from django.db import transaction
from .models import User, Role
from .models_extended import (
    EmployeeProfile, EmergencyContact, EmploymentDetails, 
    BankDetails, Branch, Department, Designation
)


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating employee details"""
    
    # User fields
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False, allow_blank=True)
    role = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        required=False,
        allow_null=True
    )
    
    # Employee Profile fields
    father_name = serializers.CharField(required=False)
    mother_name = serializers.CharField(required=False)
    date_of_birth = serializers.DateField(required=False)
    gender = serializers.CharField(required=False)
    date_of_joining = serializers.DateField(required=False)
    height_cm = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    weight_kg = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    blood_group = serializers.CharField(required=False)
    marital_status = serializers.CharField(required=False)
    official_email = serializers.EmailField(required=False, allow_blank=True)
    contact_number = serializers.CharField(required=False)
    another_contact_number = serializers.CharField(required=False, allow_blank=True)
    pan_number = serializers.CharField(required=False, allow_blank=True)
    uid_number = serializers.CharField(required=False, allow_blank=True)
    una_number = serializers.CharField(required=False, allow_blank=True)
    esic_number = serializers.CharField(required=False, allow_blank=True)
    pf_number = serializers.CharField(required=False, allow_blank=True)
    qualification = serializers.CharField(required=False)
    present_address = serializers.CharField(required=False)
    present_city = serializers.CharField(required=False)
    present_state = serializers.CharField(required=False)
    present_pincode = serializers.CharField(required=False)
    same_as_present_address = serializers.BooleanField(required=False)
    permanent_address = serializers.CharField(required=False)
    permanent_city = serializers.CharField(required=False)
    permanent_state = serializers.CharField(required=False)
    permanent_pincode = serializers.CharField(required=False)
    
    # Emergency Contact fields
    relationship_name = serializers.CharField(required=False)
    relationship_type = serializers.CharField(required=False)
    parent_mobile = serializers.CharField(required=False)
    emergency_another_mobile = serializers.CharField(required=False, allow_blank=True)
    
    # Employment Details fields
    branch = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    department = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    designation = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    grade = serializers.CharField(required=False, allow_blank=True)
    grade_level = serializers.IntegerField(required=False, allow_null=True)
    employment_type = serializers.CharField(required=False)
    reporting_officer = serializers.IntegerField(required=False, allow_null=True)
    deputed_project = serializers.CharField(required=False, allow_blank=True)
    effective_date = serializers.DateField(required=False)
    
    # Bank Details fields
    bank_name = serializers.CharField(required=False)
    bank_branch = serializers.CharField(required=False)
    account_number = serializers.CharField(required=False)
    ifsc_code = serializers.CharField(required=False)
    is_salary_account = serializers.BooleanField(required=False)
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'role',
            'father_name', 'mother_name', 'date_of_birth', 'gender', 'date_of_joining',
            'height_cm', 'weight_kg', 'blood_group', 'marital_status',
            'official_email', 'contact_number', 'another_contact_number',
            'pan_number', 'uid_number', 'una_number', 'esic_number', 'pf_number',
            'qualification', 'present_address', 'present_city', 'present_state',
            'present_pincode', 'same_as_present_address', 'permanent_address',
            'permanent_city', 'permanent_state', 'permanent_pincode',
            'relationship_name', 'relationship_type', 'parent_mobile', 'emergency_another_mobile',
            'branch', 'department', 'designation', 'grade', 'grade_level', 'employment_type',
            'reporting_officer', 'deputed_project', 'effective_date',
            'bank_name', 'bank_branch', 'account_number', 'ifsc_code', 'is_salary_account'
        ]
    
    @transaction.atomic
    def update(self, instance, validated_data):
        # Update User fields
        user_fields = ['first_name', 'last_name', 'email', 'phone']
        for field in user_fields:
            if field in validated_data:
                value = validated_data.pop(field)
                # Check if email already exists for another user
                if field == 'email' and value != instance.email:
                    if User.objects.filter(email=value).exclude(id=instance.id).exists():
                        raise serializers.ValidationError({"email": "This email is already in use."})
                setattr(instance, field, value)
        
        if 'role' in validated_data:
            instance.role = validated_data.pop('role')
        
        instance.save()
        
        # Update Employee Profile
        profile_fields = [
            'father_name', 'mother_name', 'date_of_birth', 'gender', 'date_of_joining',
            'height_cm', 'weight_kg', 'blood_group', 'marital_status',
            'official_email', 'contact_number', 'another_contact_number',
            'pan_number', 'uid_number', 'una_number', 'esic_number', 'pf_number',
            'qualification', 'present_address', 'present_city', 'present_state',
            'present_pincode', 'same_as_present_address', 'permanent_address',
            'permanent_city', 'permanent_state', 'permanent_pincode'
        ]
        
        profile_data = {field: validated_data.pop(field) for field in profile_fields if field in validated_data}
        
        if profile_data:
            try:
                profile = instance.employee_profile
                for field, value in profile_data.items():
                    setattr(profile, field, value)
                profile.save()
            except EmployeeProfile.DoesNotExist:
                # Create profile if it doesn't exist
                EmployeeProfile.objects.create(user=instance, **profile_data)
        
        # Update Emergency Contact
        emergency_fields = {
            'relationship_name': validated_data.pop('relationship_name', None),
            'relationship_type': validated_data.pop('relationship_type', None),
            'parent_mobile': validated_data.pop('parent_mobile', None),
            'another_mobile': validated_data.pop('emergency_another_mobile', None),
        }
        emergency_fields = {k: v for k, v in emergency_fields.items() if v is not None}
        
        if emergency_fields:
            try:
                profile = instance.employee_profile
                try:
                    emergency = profile.emergency_contact
                    for field, value in emergency_fields.items():
                        setattr(emergency, field, value)
                    emergency.save()
                except EmergencyContact.DoesNotExist:
                    EmergencyContact.objects.create(employee=profile, **emergency_fields)
            except EmployeeProfile.DoesNotExist:
                pass
        
        # Update Employment Details
        employment_fields = {}
        if 'branch' in validated_data:
            branch_val = validated_data.pop('branch')
            branch_obj = None
            if branch_val:
                branch_val_str = str(branch_val).strip()
                if branch_val_str:
                    if branch_val_str.isdigit():
                        branch_obj = Branch.objects.filter(id=int(branch_val_str)).first()
                    if not branch_obj:
                        branch_obj, _ = Branch.objects.get_or_create(
                            name=branch_val_str,
                            defaults={'code': branch_val_str[:20].upper()}
                        )
            employment_fields['branch'] = branch_obj

        if 'department' in validated_data:
            dept_val = validated_data.pop('department')
            dept_obj = None
            if dept_val:
                dept_val_str = str(dept_val).strip()
                if dept_val_str:
                    if dept_val_str.isdigit():
                        dept_obj = Department.objects.filter(id=int(dept_val_str)).first()
                    if not dept_obj:
                        dept_obj, _ = Department.objects.get_or_create(
                            name=dept_val_str,
                            defaults={'code': dept_val_str[:20].upper()}
                        )
            employment_fields['department'] = dept_obj

        if 'designation' in validated_data:
            desig_val = validated_data.pop('designation')
            desig_obj = None
            if desig_val:
                desig_val_str = str(desig_val).strip()
                if desig_val_str:
                    if desig_val_str.isdigit():
                        desig_obj = Designation.objects.filter(id=int(desig_val_str)).first()
                    if not desig_obj:
                        desig_obj, _ = Designation.objects.get_or_create(
                            name=desig_val_str,
                            defaults={'code': desig_val_str[:20].upper()}
                        )
            employment_fields['designation'] = desig_obj
        if 'grade' in validated_data:
            employment_fields['grade'] = validated_data.pop('grade')
        if 'grade_level' in validated_data:
            gl_id = validated_data.pop('grade_level')
            if gl_id:
                from .models_extended import GradePayLevel
                try:
                    gl = GradePayLevel.objects.get(id=gl_id)
                    employment_fields['grade_level'] = gl
                    # Sync legacy text field if not explicitly provided
                    if 'grade' not in employment_fields:
                        employment_fields['grade'] = gl.name
                except GradePayLevel.DoesNotExist:
                    pass
            else:
                employment_fields['grade_level'] = None
        if 'employment_type' in validated_data:
            employment_fields['employment_type'] = validated_data.pop('employment_type')
        if 'grade_level' in validated_data and 'grade_level' not in employment_fields:
            validated_data.pop('grade_level')  # already processed above
        if 'reporting_officer' in validated_data:
            officer_id = validated_data.pop('reporting_officer')
            if officer_id:
                try:
                    employment_fields['reporting_officer'] = User.objects.get(id=officer_id)
                except User.DoesNotExist:
                    pass
            else:
                employment_fields['reporting_officer'] = None
        if 'deputed_project' in validated_data:
            employment_fields['deputed_project'] = validated_data.pop('deputed_project')
        if 'effective_date' in validated_data:
            employment_fields['effective_date'] = validated_data.pop('effective_date')
        
        if employment_fields:
            try:
                profile = instance.employee_profile
                try:
                    employment = profile.employment_details
                    for field, value in employment_fields.items():
                        setattr(employment, field, value)
                    employment.save()
                except EmploymentDetails.DoesNotExist:
                    EmploymentDetails.objects.create(employee=profile, **employment_fields)
            except EmployeeProfile.DoesNotExist:
                pass
        
        # Update Bank Details
        bank_fields = ['bank_name', 'bank_branch', 'account_number', 'ifsc_code', 'is_salary_account']
        bank_data = {field: validated_data.pop(field) for field in bank_fields if field in validated_data}
        
        if bank_data:
            try:
                profile = instance.employee_profile
                try:
                    bank = profile.bank_details
                    for field, value in bank_data.items():
                        setattr(bank, field, value)
                    bank.save()
                except BankDetails.DoesNotExist:
                    BankDetails.objects.create(employee=profile, **bank_data)
            except EmployeeProfile.DoesNotExist:
                pass
        
        return instance
