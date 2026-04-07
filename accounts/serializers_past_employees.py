from rest_framework import serializers
from .models_past_employees import PastEmployee


class PastEmployeeSerializer(serializers.ModelSerializer):
    """Serializer for past employees"""
    
    class Meta:
        model = PastEmployee
        fields = [
            'id', 'user_id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'role_name', 'profile_data', 'emergency_contact_data',
            'employment_data', 'bank_data', 'deleted_by', 'deleted_at',
            'deletion_reason', 'date_joined', 'date_of_joining', 'last_working_day'
        ]
        read_only_fields = ['id', 'deleted_at']


class DeleteEmployeeSerializer(serializers.Serializer):
    """Serializer for employee deletion with reason"""
    deletion_reason = serializers.CharField(required=False, allow_blank=True)
    last_working_day = serializers.DateField(required=False, allow_null=True)
