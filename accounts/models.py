from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class Role(models.Model):
    """Role model for role-based access control"""
    ADMIN = 'ADMIN'
    HR = 'HR'
    MANAGER = 'MANAGER'
    EMPLOYEE = 'EMPLOYEE'
    
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (HR, 'HR'),
        (MANAGER, 'Manager'),
        (EMPLOYEE, 'Employee'),
    ]
    
    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'roles'


class Permission(models.Model):
    """Permission model for granular access control"""
    name = models.CharField(max_length=100, unique=True)
    codename = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'permissions'


class UserManager(BaseUserManager):
    """Custom user manager for User model"""
    
    def create_user(self, user_id, email, password=None, **extra_fields):
        """Create and save a regular user"""
        if not email:
            raise ValueError('The Email field must be set')
        if not user_id:
            raise ValueError('The User ID field must be set')
        
        email = self.normalize_email(email)
        extra_fields.setdefault('username', user_id)
        user = self.model(user_id=user_id, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, user_id, email, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(user_id, email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model extending Django's AbstractUser"""
    user_id = models.CharField(max_length=20, unique=True, help_text="Employee ID for login")
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(max_length=15, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    permissions = models.ManyToManyField(Permission, blank=True, related_name='users')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    
    objects = UserManager()
    
    USERNAME_FIELD = 'user_id'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    def __str__(self):
        return f"{self.user_id} - {self.email}"
    
    def save(self, *args, **kwargs):
        # Auto-generate user_id if not provided
        if not self.user_id:
            # Get last employee (only those with EMP prefix)
            last_employee = User.objects.filter(user_id__startswith='EMP').order_by('id').last()
            if last_employee:
                try:
                    last_id = int(last_employee.user_id.replace('EMP', ''))
                    self.user_id = f'EMP{str(last_id + 1).zfill(4)}'
                except ValueError:
                    self.user_id = 'EMP0001'
            else:
                self.user_id = 'EMP0001'
        
        # Set username same as user_id for Django compatibility
        if not self.username:
            self.username = self.user_id
        
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'users'

