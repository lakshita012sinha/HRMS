from django.db import models
from accounts.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class SalaryStructure(models.Model):
    """CTC-based salary structure for each employee"""
    employee = models.OneToOneField(User, on_delete=models.CASCADE, related_name='salary_structure')
    
    # Grade and designation
    grade = models.CharField(max_length=50, blank=True)
    designation = models.CharField(max_length=100, blank=True)

    # CTC (Cost to Company) - Primary input
    ctc_monthly = models.DecimalField(
        max_digits=10, decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Monthly CTC amount"
    )
    
    # Auto-calculated fields based on CTC
    # Basic salary = 50% of Gross Salary
    basic_salary = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="50% of Gross Salary (Auto-calculated)"
    )
    
    # HRA = 40% of basic salary
    hra = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, 
        validators=[MinValueValidator(Decimal('0.00'))], 
        help_text="40% of basic salary (Auto-calculated)"
    )
    
    # CA = 20% of basic salary
    ca = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, 
        validators=[MinValueValidator(Decimal('0.00'))], 
        help_text="Conveyance Allowance - 20% of basic (Auto-calculated)"
    )
    
    # CCA = Gross − (Basic + HRA + CA + Bonus + Mobile)  — balancing component
    cca = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="City Compensatory Allowance — balancing component (Auto-calculated)"
    )
    
    # Bonus = 20% of basic salary
    bonus = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, 
        validators=[MinValueValidator(Decimal('0.00'))], 
        help_text="Bonus - 20% of basic (Auto-calculated)"
    )
    
    # Mobile allowance (fixed amount)
    mobile = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, 
        validators=[MinValueValidator(Decimal('0.00'))], 
        help_text="Mobile allowance (fixed)"
    )
    
    # PF calculations
    # Employee PF = 12% of basic salary
    pf_employee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, 
        validators=[MinValueValidator(Decimal('0.00'))], 
        help_text="Employee PF - 12% of basic (Auto-calculated)"
    )
    
    # Employer PF = 12% of basic salary
    pf_employer = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Employer PF - 12% of basic (Auto-calculated, deducted from CTC)"
    )
    
    # ESI calculations (only for salary <= 21000)
    # Employee ESI = gross * 0.75%
    esi_employee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, 
        validators=[MinValueValidator(Decimal('0.00'))], 
        help_text="Employee ESI - 0.75% of gross (if salary <= 21000)"
    )
    
    # Employer ESI = gross * 3.25%
    esi_employer = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, 
        validators=[MinValueValidator(Decimal('0.00'))], 
        help_text="Employer ESI - 3.25% of gross (if salary <= 21000)"
    )
    
    # Other deductions
    other_deductions = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, 
        validators=[MinValueValidator(Decimal('0.00'))], 
        help_text="Other deductions"
    )
    
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField(help_text="Date from which this salary structure is effective")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """Auto-calculate salary components from CTC using the following rules:

        CTC = Gross Salary + Employer PF + Employer ESI

        Gross Salary = Basic + HRA + CA + Bonus + Mobile + CCA
        Basic  = 50% of Gross
        HRA    = 40% of Basic  (= 20% of Gross)
        CA     = 20% of Basic  (= 10% of Gross)
        Bonus  = 20% of Basic  (= 10% of Gross)
        Mobile = ₹500 (fixed)
        CCA    = Gross − (Basic + HRA + CA + Bonus + Mobile)  ← balancing component

        PF:
          Employee PF = 12% × Basic
          Employer PF = 12% × Basic

        ESI (only when Gross ≤ ESI_WAGE_LIMIT = 21,000):
          Employee ESI = 0.75% × Gross
          Employer ESI = 3.25% × Gross

        Deriving Gross from CTC:
          CTC = Gross × (1 + 0.12×0.5)  [+ Employer ESI if applicable]
              = Gross × 1.06             (if Gross > 21,000 — no ESI)
              = Gross × 1.0925           (if Gross ≤ 21,000 — ESI applies)
        """
        ESI_WAGE_LIMIT = Decimal('21000.00')
        R = Decimal('0.01')  # rounding quantum

        # ── Step 1: Determine whether ESI applies by first estimating Gross ────
        # Estimate without ESI: Gross ≈ CTC / 1.06
        gross_estimate = (self.ctc_monthly / Decimal('1.06')).quantize(R)
        esi_applies = gross_estimate <= ESI_WAGE_LIMIT

        # If ESI might apply, refine with the ESI divisor
        if esi_applies:
            gross_estimate = (self.ctc_monthly / Decimal('1.0925')).quantize(R)
            # Edge case: after ESI divisor the gross might flip above the limit
            # In that case fall back to no-ESI divisor
            if gross_estimate > ESI_WAGE_LIMIT:
                esi_applies = False
                gross_estimate = (self.ctc_monthly / Decimal('1.06')).quantize(R)

        gross = gross_estimate

        # ── Step 2: Derive all components from Gross ────────────────────────────
        basic = (gross * Decimal('0.50')).quantize(R)
        hra   = (basic * Decimal('0.40')).quantize(R)
        ca    = (basic * Decimal('0.20')).quantize(R)
        bonus = (basic * Decimal('0.20')).quantize(R)
        mobile = Decimal('500.00')

        # CCA is the balancing component so Gross = Basic + HRA + CA + Bonus + Mobile + CCA
        cca = (gross - basic - hra - ca - bonus - mobile).quantize(R)
        if cca < Decimal('0.00'):
            cca = Decimal('0.00')

        # ── Step 3: PF ────────────────────────────────────────────────────────────
        pf_employee = (basic * Decimal('0.12')).quantize(R)
        pf_employer = (basic * Decimal('0.12')).quantize(R)

        # ── Step 4: ESI ──────────────────────────────────────────────────────────
        if esi_applies:
            esi_employee = (gross * Decimal('0.0075')).quantize(R)
            esi_employer = (gross * Decimal('0.0325')).quantize(R)
        else:
            esi_employee = Decimal('0.00')
            esi_employer = Decimal('0.00')

        # ── Assign ───────────────────────────────────────────────────────────────
        self.basic_salary = basic
        self.hra          = hra
        self.ca           = ca
        self.cca          = cca
        self.bonus        = bonus
        self.mobile       = mobile
        self.pf_employee  = pf_employee
        self.pf_employer  = pf_employer
        self.esi_employee = esi_employee
        self.esi_employer = esi_employer

        super().save(*args, **kwargs)
    
    def calculate_gross_salary(self):
        """Calculate gross salary (what employee receives before deductions)"""
        return (self.basic_salary + self.hra + self.ca + self.cca + 
                self.bonus + self.mobile)
    
    def calculate_employee_deductions(self):
        """Calculate total employee deductions"""
        return self.pf_employee + self.esi_employee + self.other_deductions
    
    def calculate_net_salary(self):
        """Calculate net salary (take-home)"""
        return self.calculate_gross_salary() - self.calculate_employee_deductions()
    
    def calculate_total_employer_cost(self):
        """Calculate total employer cost (CTC)"""
        return self.calculate_gross_salary() + self.pf_employer + self.esi_employer
    
    def get_ctc_breakdown(self):
        """Get detailed CTC breakdown"""
        gross = self.calculate_gross_salary()
        return {
            'ctc_monthly': float(self.ctc_monthly),
            'basic_salary': float(self.basic_salary),
            'hra': float(self.hra),
            'ca': float(self.ca),
            'cca': float(self.cca),
            'bonus': float(self.bonus),
            'mobile': float(self.mobile),
            'gross_salary': float(gross),
            'pf_employee': float(self.pf_employee),
            'pf_employer': float(self.pf_employer),
            'esi_employee': float(self.esi_employee),
            'esi_employer': float(self.esi_employer),
            'other_deductions': float(self.other_deductions),
            'total_employee_deductions': float(self.calculate_employee_deductions()),
            'net_salary': float(self.calculate_net_salary()),
            'total_employer_cost': float(self.calculate_total_employer_cost())
        }
    
    def __str__(self):
        return f"{self.employee.user_id} - Salary Structure"
    
    class Meta:
        db_table = 'salary_structures'
        verbose_name_plural = 'Salary Structures'


class Salary(models.Model):
    """Monthly salary record for employees"""
    STATUS_CHOICES = [
        ('GENERATED', 'Generated'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='salaries')
    month = models.IntegerField(validators=[MinValueValidator(1)], help_text="Month (1-12)")
    year = models.IntegerField(validators=[MinValueValidator(2000)], help_text="Year")
    
    # CTC and salary components
    ctc_monthly = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    hra = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    ca = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    cca = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    mobile = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    
    # PF breakdown
    pf_employee = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))], help_text="Employee PF (12% of basic)")
    pf_employer = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))], help_text="Employer PF (13% of basic)")
    
    # ESI breakdown
    esi_employee = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))], help_text="Employee ESI (0.75% of gross if applicable)")
    esi_employer = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))], help_text="Employer ESI (3.25% of gross if applicable)")
    
    # Other deductions
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], help_text="Total employee deductions")
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='GENERATED')
    paid_days = models.DecimalField(max_digits=5, decimal_places=1, default=0, help_text="Actual paid days (present + sundays)")
    payment_date = models.DateField(null=True, blank=True, help_text="Date when salary was paid")
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.user_id} - {self.month}/{self.year} - {self.status}"
    
    class Meta:
        db_table = 'salaries'
        unique_together = ['employee', 'month', 'year']
        ordering = ['-year', '-month']
        verbose_name_plural = 'Salaries'


class SalaryGrade(models.Model):
    """Salary grade/pay scale definition"""
    grade = models.CharField(max_length=50)
    designation = models.CharField(max_length=100, blank=True)
    basic_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'salary_grades'
        ordering = ['grade']

    def __str__(self):
        return f"{self.grade} - {self.designation}"
