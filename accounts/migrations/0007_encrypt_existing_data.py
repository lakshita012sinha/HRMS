from django.db import migrations
from cryptography.fernet import Fernet
from django.conf import settings

def encrypt_fields(apps, schema_editor):
    EmployeeProfile = apps.get_model('accounts', 'EmployeeProfile')
    
    if not getattr(settings, 'FIELD_ENCRYPTION_KEY', None):
        print("FIELD_ENCRYPTION_KEY not set. Skipping encryption migration.")
        return
        
    cipher = Fernet(settings.FIELD_ENCRYPTION_KEY.encode())
    
    def is_encrypted(val):
        if not val:
            return False
        try:
            cipher.decrypt(str(val).encode())
            return True
        except Exception:
            return False

    def encrypt_val(val):
        if not val or is_encrypted(val):
            return val
        return cipher.encrypt(str(val).encode()).decode()

    for profile in EmployeeProfile.objects.all():
        updated = False
        for field in ['pan_number', 'uid_number', 'una_number', 'esic_number', 'pf_number']:
            val = getattr(profile, field)
            if val and not is_encrypted(val):
                setattr(profile, field, encrypt_val(val))
                updated = True
        if updated:
            profile.save()

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_alter_employeeprofile_esic_number_and_more'),
    ]

    operations = [
        migrations.RunPython(encrypt_fields, reverse_code=migrations.RunPython.noop),
    ]
