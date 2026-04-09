from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('asset_management', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE asset_zones ADD COLUMN city VARCHAR(100) NOT NULL DEFAULT '';",
            reverse_sql="SELECT 1;",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE asset_zones ADD COLUMN state VARCHAR(100) NOT NULL DEFAULT '';",
            reverse_sql="SELECT 1;",
        ),
    ]
