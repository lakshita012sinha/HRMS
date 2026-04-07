from django.db import models
from accounts.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class SalaryStructure(models.Model):
    """CTC-based salary structure for each employee"""
    employee = models.OneToOneField(User, on_delete=models.CASCADE, related_name='salary_structure')
    
    # CTC (Cost to Company) - Primary input
    ctc_monthly = models.DecimalField(
        max_digits=10, decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Monthly CTC amount"
    )
    
    # Auto-calculated fields based on CTC
    # Basic salary = 46.95% of CTC
    basic_salary = models.DecimalField(
        max_digits=10, decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="46.95% of CTC (Auto-calculated)"
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
    
    # CCA = 13-15% of basic salary (default 15.74%)
    cca = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, 
        validators=[MinValueValidator(Decimal('0.00'))], 
        help_text="Communication/Clothing Allowance - 15.74% of basic (Auto-calculated)"
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
    
    # Employer PF = 13% of basic salary (deducted from CTC)
    pf_employer = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, 
        validators=[MinValueValidator(Decimal('0.00'))], 
        help_text="Employer PF - 13% of basic (Auto-calculated, deducted from CTC)"
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
        """Auto-calculate salary components based on CTC
        
        Formula: CTC = Gross Salary + Employer PF + Employer ESI
        Where: Gross = Basic + HRA + CA + CCA + Bonus + Mobile
        
        Components calculated from CTC:
        - Basic = 46.95% of CTC
        - HRA = 40% of Basic
        - CA = 20% of Basic
        - Bonus = 20% of Basic
        - Mobile = 500 (fixed)
        - CCA = Auto-adjusted to balance equation
        
        Employer contributions (from employee salary):
        - Employer PF = 13% of Basic Salary
        - Employer ESI = 3.25% of Gross Salary (only if Gross <= 21000)
        
        Employee deductions:
        - Employee PF = 12% of Basic
        - Employee ESI = 0.75% of Gross (only if Gross <= 21000)
        """
        # Iterative calculation to handle CCA dependency
        # CCA depends on Employer ESI, which depends on Gross
        
        for iteration in range(5):  # Max 5 iterations for convergence
            # Step 1: Calculate basic salary as percentage of CTC
            self.basic_salary = self.ctc_monthly * Decimal('0.4695')
            
            # Step 2: Calculate fixed allowances based on basic salary
            self.hra = self.basic_salary * Decimal('0.40')
            self.ca = self.basic_salary * Decimal('0.20')
            self.bonus = self.basic_salary * Decimal('0.20')
            
            # Step 3: Mobile is always 500
            self.mobile = Decimal('500')
            
            # Step 4: Calculate employee PF (12% of basic)
            self.pf_employee = self.basic_salary * Decimal('0.12')
            
            # Step 5: Calculate employer PF (13% of basic salary)
            self.pf_employer = self.basic_salary * Decimal('0.13')
            
            # Step 6: Calculate gross salary without CCA
            gross_without_cca = (self.basic_salary + self.hra + self.ca + 
                                self.bonus + self.mobile)
            
            # Step 7: Calculate ESI based on gross salary
            # ESI is only applicable if gross <= 21000
            if gross_without_cca <= Decimal('21000'):
                self.esi_employee = gross_without_cca * Decimal('0.0075')
                # Employer ESI = 3.25% of Gross Salary (when applicable)
                self.esi_employer = gross_without_cca * Decimal('0.0325')
            else:
                self.esi_employee = Decimal('0.00')
                self.esi_employer = Decimal('0.00')
            
            # Step 8: Calculate CCA to balance the CTC equation
            # CTC = Basic + HRA + CA + Bonus + Mobile + CCA + Employer PF + Employer ESI
            # CCA = CTC - (Basic + HRA + CA + Bonus + Mobile + Employer PF + Employer ESI)
            components_without_cca = (self.basic_salary + self.hra + self.ca + 
                                      self.bonus + self.mobile + self.pf_employer + 
                                      self.esi_employer)
            self.cca = self.ctc_monthly - components_without_cca
        
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
