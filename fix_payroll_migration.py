"""
Script to fix payroll migration and update database
"""
import os
import django
import sqlite3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from django.conf import settings
from django.core.management import call_command

# Connect to SQLite database
db_path = settings.DATABASES['default']['NAME']
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Step 1: Dropping old payroll tables...")
try:
    cursor.execute("DROP TABLE IF EXISTS salaries")
    cursor.execute("DROP TABLE IF EXISTS salary_structures")
    conn.commit()
    print("✓ Old tables dropped")
except Exception as e:
    print(f"Error dropping tables: {e}")

print("\nStep 2: Removing migration records...")
try:
    cursor.execute("DELETE FROM django_migrations WHERE app = 'payroll'")
    conn.commit()
    print("✓ Migration records removed")
except Exception as e:
    print(f"Error removing migrations: {e}")

conn.close()

print("\nStep 3: Creating new migration...")
try:
    call_command('makemigrations', 'payroll')
    print("✓ Migration created")
except Exception as e:
    print(f"Error creating migration: {e}")

print("\nStep 4: Applying migration...")
try:
    call_command('migrate', 'payroll')
    print("✓ Migration applied")
except Exception as e:
    print(f"Error applying migration: {e}")

print("\n✅ Done! You can now test the API.")
