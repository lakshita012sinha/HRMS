from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, Permission
from .models_extended import GradePayLevel


@admin.register(GradePayLevel)
class GradePayLevelAdmin(admin.ModelAdmin):
    list_display  = ['name', 'min_ctc', 'max_ctc', 'description', 'is_active', 'created_at']
    list_filter   = ['is_active']
    search_fields = ['name']
    ordering      = ['min_ctc']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['user_id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff']
    list_filter = ['role', 'is_active', 'is_staff', 'created_at']
    search_fields = ['user_id', 'email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_id', 'phone', 'role', 'permissions', 'created_by')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('user_id', 'email', 'phone', 'role')}),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'codename', 'created_at']
    search_fields = ['name', 'codename']
