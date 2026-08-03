"""
Seed the initial E1–E5 Grade/Pay Level master rows.
The migration is reversible — it deletes only the rows it created.
"""
from django.db import migrations


GRADES = [
    # (name, min_ctc, max_ctc, description)
    ("E1",  15_000,   25_000,  "Entry level — ₹15,000 to ₹25,000 monthly CTC"),
    ("E2",  25_001,   40_000,  "Junior level — ₹25,001 to ₹40,000 monthly CTC"),
    ("E3",  40_001,   60_000,  "Mid level — ₹40,001 to ₹60,000 monthly CTC"),
    ("E4",  60_001, 1_00_000,  "Senior level — ₹60,001 to ₹1,00,000 monthly CTC"),
    ("E5", 1_00_001,   None,   "Leadership level — Above ₹1,00,000 monthly CTC"),
]


def seed(apps, schema_editor):
    GradePayLevel = apps.get_model("accounts", "GradePayLevel")
    for name, mn, mx, desc in GRADES:
        GradePayLevel.objects.get_or_create(
            name=name,
            defaults={"min_ctc": mn, "max_ctc": mx, "description": desc, "is_active": True},
        )


def unseed(apps, schema_editor):
    GradePayLevel = apps.get_model("accounts", "GradePayLevel")
    GradePayLevel.objects.filter(name__in=[g[0] for g in GRADES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0010_add_grade_pay_level"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
