"""
Update E1 and E2 CTC ranges:
  E1 → ₹0 – ₹22,000   (ESIC applicable — CTC ≤ ₹21,000 threshold)
  E2 → ₹23,000 – ₹40,000

E3, E4, E5 and PF rules are unchanged.
"""
from django.db import migrations


def update_ranges(apps, schema_editor):
    GradePayLevel = apps.get_model("accounts", "GradePayLevel")

    GradePayLevel.objects.filter(name="E1").update(
        min_ctc=0,
        max_ctc=22_000,
        description="Entry level — ₹0 to ₹22,000 monthly CTC (ESIC applicable)",
    )
    GradePayLevel.objects.filter(name="E2").update(
        min_ctc=23_000,
        max_ctc=40_000,
        description="Junior level — ₹23,000 to ₹40,000 monthly CTC",
    )


def revert_ranges(apps, schema_editor):
    GradePayLevel = apps.get_model("accounts", "GradePayLevel")

    GradePayLevel.objects.filter(name="E1").update(
        min_ctc=15_000,
        max_ctc=25_000,
        description="Entry level — ₹15,000 to ₹25,000 monthly CTC",
    )
    GradePayLevel.objects.filter(name="E2").update(
        min_ctc=25_001,
        max_ctc=40_000,
        description="Junior level — ₹25,001 to ₹40,000 monthly CTC",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0011_seed_grade_pay_levels"),
    ]

    operations = [
        migrations.RunPython(update_ranges, revert_ranges),
    ]
