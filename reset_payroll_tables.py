"""
Script to reset payroll tables and create fresh migrations
"""
import os
import django
import sqlite3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from django.conf import settings

# Connect to SQLite database
db_path = settings.DATABASES['default']['NAME']
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Drop payroll tables if they exist
    cursor.execute("DROP TABLE IF EXISTS salaries")
    cursor.execute("DROP TABLE IF EXISTS salary_structures")
    
    # Remove payroll migration records
    cursor.execute("DELETE FROM django_migrations WHERE app = 'payroll'")
    
    conn.commit()
    print("✓ Payroll tables and migration records removed")
    
except Exception as e:
    print(f"Error: {e}")
    
finally:
    conn.close()

print("Now run: python manage.py makemigrations payroll")
print("Then run: python manage.py migrate")