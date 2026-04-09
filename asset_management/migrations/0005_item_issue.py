from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('asset_management', '0004_purchase')]
    operations = [
        migrations.RunSQL(
            sql="""CREATE TABLE IF NOT EXISTS asset_item_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                office_id INTEGER NULL REFERENCES asset_zones(id) ON DELETE SET NULL,
                employee_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
                item_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
                quantity INTEGER NOT NULL DEFAULT 1,
                issue_date DATE NOT NULL,
                returnable BOOLEAN NOT NULL DEFAULT 0,
                remark TEXT NOT NULL DEFAULT '',
                created_by_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );""",
            reverse_sql="DROP TABLE IF EXISTS asset_item_issues;",
        ),
    ]
