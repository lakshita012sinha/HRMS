from django.db import models
from accounts.models import User
from django.utils import timezone
from datetime import timedelta


class Shift(models.Model):
    """Shift model for different work timings"""
    shift_name = models.CharField(max_length=50, unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    half_day_hours = models.DecimalField(max_digits=4, decimal_places=2, default=4.0)
    full_day_hours = models.DecimalField(max_digits=4, decimal_places=2, default=8.0)
    weekly_off_days = models.CharField(max_length=100, help_text="Comma-separated days (e.g., Saturday,Sunday)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.shift_name} ({self.start_time} - {self.end_time})"
    
    class Meta:
        db_table = 'shifts'


class EmployeeShiftAssignment(models.Model):
    """Assign shifts to employees"""
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shift_assignments')
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='employee_assignments')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text="Leave blank for ongoing assignment")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.user_id} - {self.shift.shift_name}"
    
    class Meta:
        db_table = 'employee_shift_assignments'
        ordering = ['-start_date']


class Holiday(models.Model):
    """Company holidays"""
    holiday_name = models.CharField(max_length=100)
    date = models.DateField(unique=True)
    description = models.TextField(blank=True)
    is_optional = models.BooleanField(default=False, help_text="Optional holiday that employees can choose")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.holiday_name} - {self.date}"
    
    class Meta:
        db_table = 'holidays'
        ordering = ['-date']


class Attendance(models.Model):
    """Main attendance table"""
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('HALF_DAY', 'Half Day'),
        ('LEAVE', 'Leave'),
        ('HOLIDAY', 'Holiday'),
        ('WEEKEND', 'Weekend'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Total working hours")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABSENT')
    location = models.CharField(max_length=255, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_total_hours(self):
        """Calculate total working hours"""
        if self.check_in_time and self.check_out_time:
            delta = self.check_out_time - self.check_in_time
            # Subtract break time (assuming 1 hour break)
            total_seconds = delta.total_seconds() - 3600
            self.total_hours = round(total_seconds / 3600, 2)
        return self.total_hours
    
    def __str__(self):
        return f"{self.employee.user_id} - {self.date} - {self.status}"
    
    class Meta:
        db_table = 'attendance'
        unique_together = ['employee', 'date']
        ordering = ['-date']


class AttendanceLog(models.Model):
    """Check-in/Check-out logs with GPS tracking"""
    LOG_TYPE_CHOICES = [
        ('CHECK_IN', 'Check In'),
        ('CHECK_OUT', 'Check Out'),
        ('BREAK_START', 'Break Start'),
        ('BREAK_END', 'Break End'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_logs')
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='logs', null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    log_type = models.CharField(max_length=20, choices=LOG_TYPE_CHOICES)
    location = models.CharField(max_length=255, blank=True)
    device = models.CharField(max_length=100, blank=True, help_text="Device info (mobile/web)")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.employee.user_id} - {self.log_type} - {self.timestamp}"
    
    class Meta:
        db_table = 'attendance_logs'
        ordering = ['-timestamp']


class GeoTracking(models.Model):
    """GPS location tracking for attendance"""
    attendance_log = models.OneToOneField(AttendanceLog, on_delete=models.CASCADE, related_name='geo_tracking')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.TextField(blank=True)
    accuracy = models.DecimalField(max_digits=10, decimal_places=2, help_text="GPS accuracy in meters")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.attendance_log.employee.user_id} - ({self.latitude}, {self.longitude})"
    
    class Meta:
        db_table = 'geo_tracking'


class AttendanceRegularization(models.Model):
    """Attendance correction requests"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='regularization_requests')
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='regularizations')
    requested_check_in = models.DateTimeField()
    requested_check_out = models.DateTimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_regularizations')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.user_id} - {self.attendance.date} - {self.status}"
    
    class Meta:
        db_table = 'attendance_regularizations'
        ordering = ['-created_at']
