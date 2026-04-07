"""
Script to create master data (Branch, Department, Designation)
Run this with: python create_master_data.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from accounts.models_extended import Branch, Department, Designation

def create_master_data():
    print("Creating Master Data...")
    
    # Create Branches
    branches = [
        {'name': 'Jaipur Branch', 'code': 'JPR001', 'address': 'Jaipur, Rajasthan'},
        {'name': 'Delhi Branch', 'code': 'DEL001', 'address': 'Delhi'},
        {'name': 'Mumbai Branch', 'code': 'MUM001', 'address': 'Mumbai, Maharashtra'},
    ]
    
    for branch_data in branches:
        branch, created = Branch.objects.get_or_create(
            code=branch_data['code'],
            defaults=branch_data
        )
        if created:
            print(f"✓ Created Branch: {branch.name} (ID: {branch.id})")
        else:
            print(f"  Branch already exists: {branch.name} (ID: {branch.id})")
    
    # Create Departments
    departments = [
        {'name': 'IT Department', 'code': 'IT001', 'description': 'Information Technology'},
        {'name': 'HR Department', 'code': 'HR001', 'description': 'Human Resources'},
        {'name': 'Finance Department', 'code': 'FIN001', 'description': 'Finance and Accounts'},
        {'name': 'Operations', 'code': 'OPS001', 'description': 'Operations'},
    ]
    
    for dept_data in departments:
        dept, created = Department.objects.get_or_create(
            code=dept_data['code'],
            defaults=dept_data
        )
        if created:
            print(f"✓ Created Department: {dept.name} (ID: {dept.id})")
        else:
            print(f"  Department already exists: {dept.name} (ID: {dept.id})")
    
    # Create Designations
    designations = [
        {'name': 'Software Engineer', 'code': 'SE001', 'description': 'Software Development'},
        {'name': 'Senior Software Engineer', 'code': 'SSE001', 'description': 'Senior Software Development'},
        {'name': 'HR Manager', 'code': 'HRM001', 'description': 'Human Resources Management'},
        {'name': 'Accountant', 'code': 'ACC001', 'description': 'Accounting'},
        {'name': 'Team Lead', 'code': 'TL001', 'description': 'Team Leadership'},
        {'name': 'Manager', 'code': 'MGR001', 'description': 'Management'},
    ]
    
    for desig_data in designations:
        desig, created = Designation.objects.get_or_create(
            code=desig_data['code'],
            defaults=desig_data
        )
        if created:
            print(f"✓ Created Designation: {desig.name} (ID: {desig.id})")
        else:
            print(f"  Designation already exists: {desig.name} (ID: {desig.id})")
    
    print("\n" + "="*60)
    print("Master Data Created Successfully!")
    print("="*60)
    print("\nYou can now use these IDs in employee registration:")
    print("\nBranches:")
    for branch in Branch.objects.all():
        print(f"  ID: {branch.id} - {branch.name}")
    print("\nDepartments:")
    for dept in Department.objects.all():
        print(f"  ID: {dept.id} - {dept.name}")
    print("\nDesignations:")
    for desig in Designation.objects.all():
        print(f"  ID: {desig.id} - {desig.name}")
    print("="*60)

if __name__ == '__main__':
    create_master_data()
