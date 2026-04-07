from django.db import models
from accounts.models import User
from django.utils import timezone
from datetime import timedelta


class LeaveType(models.Model):
    """Leave type model - Casual, Sick, Earned, etc."""
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    max_days_per_year = models.IntegerField(default=0, help_text="Maximum days allowed per year")
    is_paid = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'leave_types'


class LeaveBalance(models.Model):
    """Track leave balance for each employee"""
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='balances')
    year = models.IntegerField(help_text="Year for which balance is tracked")
    total_allocated = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    used = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    available = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_available(self):
        """Calculate available leave balance"""
        self.available = self.total_allocated - self.used
        return self.available
    
    def __str__(self):
        return f"{self.employee.user_id} - {self.leave_type.name} - {self.year}"
    
    class Meta:
        db_table = 'leave_balances'
        unique_together = ['employee', 'leave_type', 'year']
        ordering = ['-year']


class LeaveRequest(models.Model):
    """Leave request model"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='requests')
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_total_days(self):
        """Calculate total leave days"""
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            self.total_days = delta.days + 1  # Include both start and end date
        return self.total_days
    
    def __str__(self):
        return f"{self.employee.user_id} - {self.leave_type.name} - {self.start_date} to {self.end_date}"
    
    class Meta:
        db_table = 'leave_requests'
        ordering = ['-created_at']


class LeavePolicy(models.Model):
    """Leave policy configuration"""
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='policies')
    min_notice_days = models.IntegerField(default=0, help_text="Minimum days notice required")
    max_consecutive_days = models.IntegerField(default=0, help_text="Maximum consecutive days allowed")
    can_carry_forward = models.BooleanField(default=False)
    max_carry_forward_days = models.IntegerField(default=0)
    applicable_after_months = models.IntegerField(default=0, help_text="Applicable after X months of joining")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Policy - {self.leave_type.name}"
    
    class Meta:
        db_table = 'leave_policies'
        verbose_name_plural = 'Leave Policies'
