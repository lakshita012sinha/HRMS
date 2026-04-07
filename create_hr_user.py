"""
Script to create HR user and get authentication token
Run this with: python create_hr_user.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from accounts.models import User, Role
from rest_framework.authtoken.models import Token

def create_hr_user():
    print("Creating HR User...")
    
    # Get or create HR role
    hr_role, created = Role.objects.get_or_create(
        name='HR',
        defaults={'description': 'HR personnel with employee management access'}
    )
    
    # Check if HR user already exists
    if User.objects.filter(user_id='HR001').exists():
        print("HR user already exists!")
        user = User.objects.get(user_id='HR001')
    else:
        # Create HR user
        user = User.objects.create_user(
            user_id='HR001',
            email='hr@company.com',
            password='HRPassword123!',
            first_name='HR',
            last_name='Manager',
            role=hr_role,
            is_staff=True,
            is_active=True
        )
        print("HR User Created Successfully!")
    
    # Get or create token
    token, created = Token.objects.get_or_create(user=user)
    
    print("\n" + "="*60)
    print("HR USER CREDENTIALS")
    print("="*60)
    print(f"User ID: {user.user_id}")
    print(f"Email: {user.email}")
    print(f"Password: HRPassword123!")
    print(f"\nAuthentication Token: {token.key}")
    print("="*60)
    print("\nUse this token in Postman:")
    print(f"Authorization: Token {token.key}")
    print("="*60)

if __name__ == '__main__':
    create_hr_user()
