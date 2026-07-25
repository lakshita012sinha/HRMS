from django.db import models
from .models import User
from .choices import (
    GENDER_CHOICES, BLOOD_GROUP_CHOICES, MARITAL_STATUS_CHOICES,
    QUALIFICATION_CHOICES, STATE_CHOICES, GRADE_CHOICES,
    EMPLOYMENT_TYPE_CHOICES, PROJECT_CHOICES, RELATIONSHIP_TYPE_CHOICES
)
from .encrypted_fields import EncryptedCharField

class Branch(models.Model):
    """Branch model"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'branches'
        verbose_name_plural = 'Branches'


class Department(models.Model):
    """Department model"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'departments'


class Designation(models.Model):
    """Designation model"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'designations'


class EmployeeProfile(models.Model):
    """Extended employee profile with all personal details"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')

    # Profile Photo
    profile_photo = models.ImageField(upload_to='employee_photos/', null=True, blank=True)

    # Personal Information
    father_name = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_joining = models.DateField()
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES)
    marital_status = models.CharField(max_length=15, choices=MARITAL_STATUS_CHOICES)
    
    # Contact Information
    official_email = models.EmailField(blank=True)
    contact_number = models.CharField(max_length=15)
    another_contact_number = models.CharField(max_length=15, blank=True)
    
    # Government IDs
    pan_number = EncryptedCharField(max_length=255, blank=True)
    uid_number = EncryptedCharField(max_length=255, blank=True, help_text="Aadhaar Number")
    una_number = EncryptedCharField(max_length=255, blank=True)
    esic_number = EncryptedCharField(max_length=255, blank=True)
    pf_number = EncryptedCharField(max_length=255, blank=True)
    
    # Education
    qualification = models.CharField(max_length=50, choices=QUALIFICATION_CHOICES)
    
    # Present Address
    present_address = models.TextField()
    present_city = models.CharField(max_length=100)
    present_state = models.CharField(max_length=50, choices=STATE_CHOICES)
    present_pincode = models.CharField(max_length=6)
    
    # Permanent Address
    same_as_present_address = models.BooleanField(default=False)
    permanent_address = models.TextField()
    permanent_city = models.CharField(max_length=100)
    permanent_state = models.CharField(max_length=50, choices=STATE_CHOICES)
    permanent_pincode = models.CharField(max_length=6)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    

    def __str__(self):
        return f"{self.user.user_id} - {self.user.get_full_name()}"
    
    class Meta:
        db_table = 'employee_profiles'


class EmergencyContact(models.Model):
    """Emergency contact details"""
    employee = models.OneToOneField(EmployeeProfile, on_delete=models.CASCADE, related_name='emergency_contact')
    relationship_name = models.CharField(max_length=100)
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_TYPE_CHOICES)
    parent_mobile = models.CharField(max_length=15)
    another_mobile = models.CharField(max_length=15, blank=True)
    
    def __str__(self):
        return f"{self.employee.user.user_id} - {self.relationship_name}"
    
    class Meta:
        db_table = 'emergency_contacts'



class EmploymentDetails(models.Model):
    """Employment related details"""
    employee = models.OneToOneField(EmployeeProfile, on_delete=models.CASCADE, related_name='employment_details')
    
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True)
    grade = models.CharField(max_length=20, choices=GRADE_CHOICES, blank=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES)
    reporting_officer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    deputed_project = models.CharField(max_length=100, choices=PROJECT_CHOICES, blank=True)
    effective_date = models.DateField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.user.user_id} - {self.designation}"
    
    class Meta:
        db_table = 'employment_details'


class BankDetails(models.Model):
    """Bank account details"""
    employee = models.OneToOneField(EmployeeProfile, on_delete=models.CASCADE, related_name='bank_details')
    
    bank_name = models.CharField(max_length=100)
    bank_branch = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    ifsc_code = models.CharField(max_length=11)
    is_salary_account = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.user.user_id} - {self.bank_name}"
    
    class Meta:
        db_table = 'bank_details'


class EmployeeDocument(models.Model):
    """Employee documents storage"""
    DOCUMENT_TYPES = [
        ('AADHAAR', 'Aadhaar Card'),
        ('PAN', 'PAN Card'),
        ('PHOTO', 'Passport Size Photo'),
        ('RESUME', 'Resume/CV'),
        ('EDUCATION', 'Educational Certificates'),
        ('OFFER_LETTER', 'Offer Letter'),
        ('JOINING_LETTER', 'Joining Letter'),
        ('BANK_PASSBOOK', 'Bank Passbook/Cancelled Cheque'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_file = models.FileField(upload_to='employee_documents/')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.employee.user.user_id} - {self.document_type}"
    
    class Meta:
        db_table = 'employee_documents'


class Promotion(models.Model):
    """Employee promotion history records"""
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='promotions')
    promoted_date = models.DateField()
    promoted_designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True)
    pay_level = models.CharField(max_length=50)
    basic_pay = models.CharField(max_length=50)
    effective_date_from = models.DateField()
    approved_by = models.CharField(max_length=100)
    remark = models.TextField(blank=True, null=True)
    document = models.FileField(upload_to='promotion_documents/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employee_promotions'

    def __str__(self):
        return f"{self.employee.user.user_id} - {self.promoted_designation}"


class Increment(models.Model):
    """Employee increment history records"""
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='increments')
    increment_date = models.DateField()
    increment_type = models.CharField(max_length=50)
    pay_level = models.CharField(max_length=50)
    previous_basic_pay = models.CharField(max_length=50)
    increment_amount = models.CharField(max_length=50)
    new_basic_pay = models.CharField(max_length=50)
    effective_date_from = models.DateField()
    approved_by = models.CharField(max_length=100)
    remark = models.TextField(blank=True, null=True)
    document = models.FileField(upload_to='increment_documents/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employee_increments'

    def __str__(self):
        return f"{self.employee.user.user_id} - {self.increment_type} - {self.new_basic_pay}"


class Transfer(models.Model):
    """Employee transfer history records"""
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='transfers')
    transfer_date = models.DateField()
    present_office = models.CharField(max_length=100)
    new_office = models.CharField(max_length=100)
    present_department = models.CharField(max_length=100)
    new_department = models.CharField(max_length=100)
    present_zone = models.CharField(max_length=100)
    new_zone = models.CharField(max_length=100)
    relieving_date = models.DateField()
    effective_date_from = models.DateField()
    approved_by = models.CharField(max_length=100)
    remark = models.TextField(blank=True, null=True)
    document = models.FileField(upload_to='transfer_documents/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employee_transfers'

    def __str__(self):
        return f"{self.employee.user.user_id} - {self.present_office} to {self.new_office}"



