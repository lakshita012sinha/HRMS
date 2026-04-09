from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('asset_management', '0002_zone_city_state'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE assets ADD COLUMN item_type VARCHAR(15) NOT NULL DEFAULT 'ASSET';",
            reverse_sql="SELECT 1;",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE assets ADD COLUMN min_stock_level INTEGER NOT NULL DEFAULT 0;",
            reverse_sql="SELECT 1;",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE assets ADD COLUMN item_image VARCHAR(200) NULL;",
            reverse_sql="SELECT 1;",
        ),
    ]
