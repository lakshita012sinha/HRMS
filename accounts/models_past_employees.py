from django.db import models
from .models import User


class PastEmployee(models.Model):
    """Model to store deleted/past employees"""
    
    # Original user data
    user_id = models.CharField(max_length=20)
    username = models.CharField(max_length=150)
    email = models.EmailField()
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, blank=True)
    
    # Role information
    role_name = models.CharField(max_length=50, blank=True)
    
    # Employee profile data (JSON field to store all profile data)
    profile_data = models.JSONField(null=True, blank=True)
    emergency_contact_data = models.JSONField(null=True, blank=True)
    employment_data = models.JSONField(null=True, blank=True)
    bank_data = models.JSONField(null=True, blank=True)
    
    # Deletion metadata
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='deleted_employees')
    deleted_at = models.DateTimeField(auto_now_add=True)
    deletion_reason = models.TextField(blank=True)
    
    # Original dates
    date_joined = models.DateTimeField(null=True)
    date_of_joining = models.DateField(null=True, blank=True)
    last_working_day = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'past_employees'
        ordering = ['-deleted_at']
    
    def __str__(self):
        return f"{self.user_id} - {self.first_name} {self.last_name}"
