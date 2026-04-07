from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from .models import User
from .models_extended import (
    EmployeeProfile, EmergencyContact, EmploymentDetails, 
    BankDetails, EmployeeDocument, Branch, Department, Designation
)


class CompleteEmployeeRegistrationSerializer(serializers.Serializer):
    """Complete employee registration with all details"""
    
    # Basic User Information
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    role = serializers.IntegerField(required=True)
    
    # Personal Information
    father_name = serializers.CharField(max_length=100, required=True)
    mother_name = serializers.CharField(max_length=100, required=True)
    date_of_birth = serializers.DateField(required=True)
    gender = serializers.ChoiceField(choices=['MALE', 'FEMALE', 'OTHERS'], required=True)
    date_of_joining = serializers.DateField(required=True)
    height_cm = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    weight_kg = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    blood_group = serializers.ChoiceField(
        choices=['A+', 'O+', 'B+', 'AB+', 'A-', 'O-', 'B-', 'AB-'], 
        required=True
    )
    marital_status = serializers.ChoiceField(choices=['MARRIED', 'UNMARRIED'], required=True)
    
    # Contact Information
    official_email = serializers.EmailField(required=False, allow_blank=True)
    contact_number = serializers.CharField(max_length=15, required=True)
    another_contact_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    
    # Government IDs
    pan_number = serializers.CharField(max_length=10, required=False, allow_blank=True)
    uid_number = serializers.CharField(max_length=12, required=False, allow_blank=True)
    una_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    esic_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    pf_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
    # Education
    qualification = serializers.ChoiceField(
        choices=[
            'ILLITERATE', 'NON-METRIC', 'METRIC', 'SENIOR-SECONDARY', 
            'GRADUATE', 'POST-GRADUATE', 'TECHNICAL(PROFESSIONAL)', 
            'DOCTORATE', 'DIPLOMA', 'OTHERS', 'MBA'
        ],
        required=True
    )
    
    # Present Address
    present_address = serializers.CharField(required=True)
    present_city = serializers.CharField(max_length=100, required=True)
    present_state = serializers.CharField(max_length=50, required=True)
    present_pincode = serializers.CharField(max_length=6, required=True)
    
    # Permanent Address
    same_as_present_address = serializers.BooleanField(default=False)
    permanent_address = serializers.CharField(required=True)
    permanent_city = serializers.CharField(max_length=100, required=True)
    permanent_state = serializers.CharField(max_length=50, required=True)
    permanent_pincode = serializers.CharField(max_length=6, required=True)
    
    # Emergency Contact
    relationship_name = serializers.CharField(max_length=100, required=True)
    relationship_type = serializers.ChoiceField(
        choices=['FATHER', 'MOTHER', 'SPOUSE', 'SIBLING', 'OTHERS'],
        required=True
    )
    parent_mobile = serializers.CharField(max_length=15, required=True)
    emergency_another_mobile = serializers.CharField(max_length=15, required=False, allow_blank=True)
    
    # Employment Details
    branch = serializers.IntegerField(required=False, allow_null=True)
    department = serializers.IntegerField(required=False, allow_null=True)
    designation = serializers.IntegerField(required=False, allow_null=True)
    grade = serializers.CharField(max_length=20, required=False, allow_blank=True)
    employment_type = serializers.ChoiceField(
        choices=['PROBATION', 'TRAINEE', 'PERMANENT', 'UNDER NOTICE'],
        required=True
    )
    reporting_officer = serializers.IntegerField(required=False, allow_null=True)
    deputed_project = serializers.CharField(max_length=100, required=False, allow_blank=True)
    effective_date = serializers.DateField(required=True)
    
    # Bank Details
    bank_name = serializers.CharField(max_length=100, required=True)
    bank_branch = serializers.CharField(max_length=100, required=True)
    account_number = serializers.CharField(max_length=20, required=True)
    ifsc_code = serializers.CharField(max_length=11, required=True)
    is_salary_account = serializers.BooleanField(default=True)
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Check if email already exists
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists."})
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        # Extract password
        password = validated_data.pop('password')
        validated_data.pop('password2')
        
        # Extract related data
        emergency_data = {
            'relationship_name': validated_data.pop('relationship_name'),
            'relationship_type': validated_data.pop('relationship_type'),
            'parent_mobile': validated_data.pop('parent_mobile'),
            'another_mobile': validated_data.pop('emergency_another_mobile', ''),
        }
        
        # Get reporting officer if provided
        reporting_officer_id = validated_data.pop('reporting_officer', None)
        reporting_officer = None
        if reporting_officer_id:
            try:
                reporting_officer = User.objects.get(id=reporting_officer_id)
            except User.DoesNotExist:
                reporting_officer = None
        
        employment_data = {
            'branch_id': validated_data.pop('branch', None),
            'department_id': validated_data.pop('department', None),
            'designation_id': validated_data.pop('designation', None),
            'grade': validated_data.pop('grade', ''),
            'employment_type': validated_data.pop('employment_type'),
            'reporting_officer': reporting_officer,
            'deputed_project': validated_data.pop('deputed_project', ''),
            'effective_date': validated_data.pop('effective_date'),
        }
        
        bank_data = {
            'bank_name': validated_data.pop('bank_name'),
            'bank_branch': validated_data.pop('bank_branch'),
            'account_number': validated_data.pop('account_number'),
            'ifsc_code': validated_data.pop('ifsc_code'),
            'is_salary_account': validated_data.pop('is_salary_account', True),
        }
        
        # Extract user data
        user_data = {
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'email': validated_data.pop('email'),
            'role_id': validated_data.pop('role'),
        }
        
        # Create User
        user = User(**user_data)
        user.set_password(password)
        
        # Set created_by if available in context
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user.created_by = request.user
        
        user.save()
        
        # Prepare profile data - only include fields that belong to EmployeeProfile
        profile_data = {
            'father_name': validated_data.pop('father_name'),
            'mother_name': validated_data.pop('mother_name'),
            'date_of_birth': validated_data.pop('date_of_birth'),
            'gender': validated_data.pop('gender'),
            'date_of_joining': validated_data.pop('date_of_joining'),
            'height_cm': validated_data.pop('height_cm', None),
            'weight_kg': validated_data.pop('weight_kg', None),
            'blood_group': validated_data.pop('blood_group'),
            'marital_status': validated_data.pop('marital_status'),
            'official_email': validated_data.pop('official_email', ''),
            'contact_number': validated_data.pop('contact_number'),
            'another_contact_number': validated_data.pop('another_contact_number', ''),
            'pan_number': validated_data.pop('pan_number', ''),
            'uid_number': validated_data.pop('uid_number', ''),
            'una_number': validated_data.pop('una_number', ''),
            'esic_number': validated_data.pop('esic_number', ''),
            'pf_number': validated_data.pop('pf_number', ''),
            'qualification': validated_data.pop('qualification'),
            'present_address': validated_data.pop('present_address'),
            'present_city': validated_data.pop('present_city'),
            'present_state': validated_data.pop('present_state'),
            'present_pincode': validated_data.pop('present_pincode'),
            'same_as_present_address': validated_data.pop('same_as_present_address', False),
            'permanent_address': validated_data.pop('permanent_address'),
            'permanent_city': validated_data.pop('permanent_city'),
            'permanent_state': validated_data.pop('permanent_state'),
            'permanent_pincode': validated_data.pop('permanent_pincode'),
        }
        
        # Create Employee Profile
        profile = EmployeeProfile.objects.create(user=user, **profile_data)
        
        # Create Emergency Contact
        EmergencyContact.objects.create(employee=profile, **emergency_data)
        
        # Create Employment Details
        EmploymentDetails.objects.create(employee=profile, **employment_data)
        
        # Create Bank Details
        BankDetails.objects.create(employee=profile, **bank_data)
        
        return user


class EmployeeDetailSerializer(serializers.ModelSerializer):
    """Detailed employee information"""
    role_name = serializers.CharField(source='role.name', read_only=True)
    employee_profile = serializers.SerializerMethodField()
    emergency_contact = serializers.SerializerMethodField()
    employment_details = serializers.SerializerMethodField()
    bank_details = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'user_id', 'email', 'first_name', 'last_name',
            'role', 'role_name', 'is_active', 'created_at',
            'employee_profile', 'emergency_contact', 'employment_details', 'bank_details', 'documents'
        ]
    
    def get_employee_profile(self, obj):
        try:
            profile = obj.employee_profile
            return {
                'profile_photo': profile.profile_photo.url if profile.profile_photo else None,
                'father_name': profile.father_name,
                'mother_name': profile.mother_name,
                'date_of_birth': profile.date_of_birth,
                'gender': profile.gender,
                'date_of_joining': profile.date_of_joining,
                'height_cm': str(profile.height_cm) if profile.height_cm else None,
                'weight_kg': str(profile.weight_kg) if profile.weight_kg else None,
                'blood_group': profile.blood_group,
                'marital_status': profile.marital_status,
                'official_email': profile.official_email,
                'contact_number': profile.contact_number,
                'another_contact_number': profile.another_contact_number,
                'uid_number': profile.uid_number,
                'pan_number': profile.pan_number,
                'una_number': profile.una_number,
                'esic_number': profile.esic_number,
                'pf_number': profile.pf_number,
                'qualification': profile.qualification,
                'present_address': profile.present_address,
                'present_city': profile.present_city,
                'present_state': profile.present_state,
                'present_pincode': profile.present_pincode,
                'permanent_address': profile.permanent_address,
                'permanent_city': profile.permanent_city,
                'permanent_state': profile.permanent_state,
                'permanent_pincode': profile.permanent_pincode,
            }
        except:
            return None
    
    def get_emergency_contact(self, obj):
        try:
            contact = obj.employee_profile.emergency_contact
            return {
                'relationship_name': contact.relationship_name,
                'relationship_type': contact.relationship_type,
                'parent_mobile': contact.parent_mobile,
            }
        except:
            return None
    
    def get_employment_details(self, obj):
        try:
            emp = obj.employee_profile.employment_details
            reporting = None
            if emp.reporting_officer:
                ro = emp.reporting_officer
                reporting = f"{ro.first_name} {ro.last_name} - {ro.user_id}".strip()
            return {
                'branch': emp.branch.name if emp.branch else None,
                'department': emp.department.name if emp.department else None,
                'designation': emp.designation.name if emp.designation else None,
                'employment_type': emp.employment_type,
                'effective_date': emp.effective_date,
                'grade': emp.grade,
                'deputed_project': emp.deputed_project,
                'reporting_officer': reporting,
            }
        except:
            return None
    
    def get_bank_details(self, obj):
        try:
            bank = obj.employee_profile.bank_details
            return {
                'bank_name': bank.bank_name,
                'bank_branch': bank.bank_branch,
                'account_number': bank.account_number,
                'ifsc_code': bank.ifsc_code,
                'is_salary_account': bank.is_salary_account,
            }
        except:
            return None

    def get_documents(self, obj):
        try:
            docs = obj.employee_profile.documents.all()
            return [
                {
                    'document_type': doc.get_document_type_display(),
                    'document_file': doc.document_file.url if doc.document_file else None,
                    'status': doc.get_status_display(),
                }
                for doc in docs
            ]
        except:
            return []
