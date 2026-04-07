import django, os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'hrms.settings'
sys.path.insert(0, '.')
django.setup()

from django.db import connection

# Check what tables exist
cursor = connection.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = [r[0] for r in cursor.fetchall()]
print("Tables:", tables)

# Check employee_profiles table
if 'employee_profiles' in tables:
    cursor.execute("SELECT COUNT(*) FROM employee_profiles;")
    print("employee_profiles rows:", cursor.fetchone()[0])
    cursor.execute("PRAGMA table_info(employee_profiles);")
    cols = [r[1] for r in cursor.fetchall()]
    print("Columns:", cols)
    cursor.execute("SELECT * FROM employee_profiles LIMIT 3;")
    rows = cursor.fetchall()
    for r in rows:
        print(r)
else:
    print("employee_profiles table does NOT exist")
