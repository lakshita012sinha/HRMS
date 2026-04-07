"""
Script to reset database and recreate migrations
WARNING: This will delete all data!
Run this with: python reset_database.py
"""
import os
import shutil

def reset_database():
    print("Resetting database...")
    
    # Delete database file
    if os.path.exists('db.sqlite3'):
        os.remove('db.sqlite3')
        print("✓ Deleted db.sqlite3")
    
    # Delete migration files (except __init__.py)
    migrations_dir = 'accounts/migrations'
    if os.path.exists(migrations_dir):
        for file in os.listdir(migrations_dir):
            if file != '__init__.py' and file.endswith('.py'):
                os.remove(os.path.join(migrations_dir, file))
                print(f"✓ Deleted {file}")
    
    print("\nDatabase reset complete!")
    print("\nNext steps:")
    print("1. python manage.py makemigrations")
    print("2. python manage.py migrate")
    print("3. python manage.py create_roles")
    print("4. python create_hr_user.py")

if __name__ == '__main__':
    response = input("This will delete all data. Are you sure? (yes/no): ")
    if response.lower() == 'yes':
        reset_database()
    else:
        print("Operation cancelled.")
