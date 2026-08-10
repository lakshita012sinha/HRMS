from django.db import models
from .models import User
from .choices import (
    GENDER_CHOICES, BLOOD_GROUP_CHOICES, MARITAL_STATUS_CHOICES,
    QUALIFICATION_CHOICES, STATE_CHOICES, GRADE_CHOICES,
    EMPLOYMENT_TYPE_CHOICES, PROJECT_CHOICES, RELATIONSHIP_TYPE_CHOICES
)
from .encrypted_fields import EncryptedCharField

class GradePayLevel(models.Model):
    """Dynamic Grade / Pay Level master — replaces the hardcoded GRADE_CHOICES."""
    name        = models.CharField(max_length=50, unique=True,
                                   help_text="Grade label, e.g. E1, E2, M")
    min_ctc     = models.DecimalField(max_digits=12, decimal_places=2,
                                      help_text="Minimum monthly CTC (₹)")
    max_ctc     = models.DecimalField(max_digits=12, decimal_places=2,
                                      null=True, blank=True,
                                      help_text="Maximum monthly CTC (₹). Leave blank for 'no upper limit' (e.g. E5)")
    description = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.max_ctc:
            return f"{self.name} (₹{self.min_ctc:,.0f} – ₹{self.max_ctc:,.0f})"
        return f"{self.name} (Above ₹{self.min_ctc:,.0f})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.max_ctc is not None and self.max_ctc < self.min_ctc:
            raise ValidationError("Maximum CTC cannot be less than Minimum CTC.")

    class Meta:
        db_table = 'grade_pay_levels'
        ordering = ['min_ctc']
        verbose_name = 'Grade / Pay Level'
        verbose_name_plural = 'Grade / Pay Levels'


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
    """Department model — optionally scoped to a branch"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    branch = models.ForeignKey(
        'Branch', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='departments', help_text="Leave blank for cross-branch department"
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.branch:
            return f"{self.name} ({self.branch.name})"
        return self.name

    class Meta:
        db_table = 'departments'
        unique_together = [('name', 'branch')]


class Designation(models.Model):
    """Designation model — optionally scoped to a branch/department"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    branch = models.ForeignKey(
        'Branch', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='designations', help_text="Leave blank for cross-branch designation"
    )
    department = models.ForeignKey(
        'Department', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='designations', help_text="Leave blank for cross-department designation"
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.branch:
            return f"{self.name} ({self.branch.name})"
        return self.name

    class Meta:
        db_table = 'designations'
        unique_together = [('name', 'branch')]


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
    # Legacy text grade kept for backward compatibility — new FK below is the source of truth
    grade = models.CharField(max_length=20, choices=GRADE_CHOICES, blank=True)
    grade_level = models.ForeignKey(
        GradePayLevel, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='employment_details',
        help_text="Grade / Pay Level from master table"
    )
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
    # Snapshot of the designation BEFORE this promotion — set at save time
    initial_designation = models.CharField(max_length=100, blank=True, default='',
                                           help_text="Designation held before this promotion (snapshot)")
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



