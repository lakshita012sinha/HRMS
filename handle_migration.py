import os
import django
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

# Create migration with automatic field renaming
execute_from_command_line(['manage.py', 'makemigrations', 'payroll', '--name', 'update_ctc_structure'])