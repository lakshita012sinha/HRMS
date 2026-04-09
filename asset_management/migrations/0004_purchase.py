from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('asset_management', '0003_asset_item_fields'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""CREATE TABLE IF NOT EXISTS asset_purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_number VARCHAR(50) NOT NULL DEFAULT '',
                supplier VARCHAR(200) NOT NULL DEFAULT '',
                office_id INTEGER NULL REFERENCES asset_zones(id) ON DELETE SET NULL,
                item_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
                quantity INTEGER NOT NULL DEFAULT 0,
                price_per_unit DECIMAL(10,2) NOT NULL DEFAULT 0,
                purchase_date DATE NOT NULL,
                remark TEXT NOT NULL DEFAULT '',
                created_by_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );""",
            reverse_sql="DROP TABLE IF EXISTS asset_purchases;",
        ),
    ]
