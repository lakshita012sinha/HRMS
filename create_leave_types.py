"""
Script to create default leave types
Run: python create_leave_types.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from leave_management.models import LeaveType

def create_leave_types():
    leave_types = [
        {
            'name': 'Casual Leave',
            'code': 'CL',
            'description': 'Leave for personal reasons and emergencies',
            'max_days_per_year': 12,
            'is_paid': True,
            'requires_approval': True,
        },
        {
            'name': 'Sick Leave',
            'code': 'SL',
            'description': 'Leave for medical reasons and health issues',
            'max_days_per_year': 10,
            'is_paid': True,
            'requires_approval': True,
        },
        {
            'name': 'Earned Leave',
            'code': 'EL',
            'description': 'Earned leave accumulated over time',
            'max_days_per_year': 15,
            'is_paid': True,
            'requires_approval': True,
        },
        {
            'name': 'Maternity Leave',
            'code': 'ML',
            'description': 'Leave for maternity purposes',
            'max_days_per_year': 180,
            'is_paid': True,
            'requires_approval': True,
        },
        {
            'name': 'Paternity Leave',
            'code': 'PL',
            'description': 'Leave for paternity purposes',
            'max_days_per_year': 15,
            'is_paid': True,
            'requires_approval': True,
        },
        {
            'name': 'Loss of Pay',
            'code': 'LOP',
            'description': 'Leave without pay',
            'max_days_per_year': 0,
            'is_paid': False,
            'requires_approval': True,
        },
    ]
    
    for leave_data in leave_types:
        leave_type, created = LeaveType.objects.get_or_create(
            code=leave_data['code'],
            defaults=leave_data
        )
        if created:
            print(f"✓ Created: {leave_type.name}")
        else:
            print(f"- Already exists: {leave_type.name}")
    
    print(f"\nTotal leave types: {LeaveType.objects.count()}")

if __name__ == '__main__':
    create_leave_types()
