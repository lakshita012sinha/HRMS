from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Permission class to check if user is Admin"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role and request.user.role.name == 'ADMIN'


class IsHROrAdmin(permissions.BasePermission):
    """Permission class to check if user is HR or Admin"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role and request.user.role.name in ['HR', 'ADMIN']


class IsManagerOrAbove(permissions.BasePermission):
    """Permission class to check if user is Manager, HR, or Admin"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role and request.user.role.name in ['MANAGER', 'HR', 'ADMIN']
