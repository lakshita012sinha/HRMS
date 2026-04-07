# Generated migration for CTC-based payroll system with new salary structure

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SalaryStructure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ctc_monthly', models.DecimalField(decimal_places=2, help_text='Monthly CTC amount', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('basic_salary', models.DecimalField(decimal_places=2, help_text='46.95% of CTC (Auto-calculated)', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('hra', models.DecimalField(decimal_places=2, default=0, help_text='40% of basic salary (Auto-calculated)', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('ca', models.DecimalField(decimal_places=2, default=0, help_text='Conveyance Allowance - 20% of basic (Auto-calculated)', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('cca', models.DecimalField(decimal_places=2, default=0, help_text='Communication/Clothing Allowance - 15.74% of basic (Auto-calculated)', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('bonus', models.DecimalField(decimal_places=2, default=0, help_text='Bonus - 20% of basic (Auto-calculated)', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('mobile', models.DecimalField(decimal_places=2, default=0, help_text='Mobile allowance (fixed)', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('pf_employee', models.DecimalField(decimal_places=2, default=0, help_text='Employee PF - 12% of basic (Auto-calculated)', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('pf_employer', models.DecimalField(decimal_places=2, default=0, help_text='Employer PF - 13% of basic (Auto-calculated, deducted from CTC)', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('esi_employee', models.DecimalField(decimal_places=2, default=0, help_text='Employee ESI - 0.75% of gross (if salary <= 21000)', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('esi_employer', models.DecimalField(decimal_places=2, default=0, help_text='Employer ESI - 3.25% of gross (if salary <= 21000)', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('other_deductions', models.DecimalField(decimal_places=2, default=0, help_text='Other deductions', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('is_active', models.BooleanField(default=True)),
                ('effective_from', models.DateField(help_text='Date from which this salary structure is effective')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('employee', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='salary_structure', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Salary Structures',
                'db_table': 'salary_structures',
            },
        ),
        migrations.CreateModel(
            name='Salary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.IntegerField(help_text='Month (1-12)', validators=[django.core.validators.MinValueValidator(1)])),
                ('year', models.IntegerField(help_text='Year', validators=[django.core.validators.MinValueValidator(2000)])),
                ('ctc_monthly', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('basic_salary', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('hra', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('ca', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('cca', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('bonus', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('mobile', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('gross_salary', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('pf_employee', models.DecimalField(decimal_places=2, default=0, help_text='Employee PF (12% of basic)', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('pf_employer', models.DecimalField(decimal_places=2, default=0, help_text='Employer PF (13% of basic)', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('esi_employee', models.DecimalField(decimal_places=2, default=0, help_text='Employee ESI (0.75% of gross if applicable)', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('esi_employer', models.DecimalField(decimal_places=2, default=0, help_text='Employer ESI (3.25% of gross if applicable)', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('other_deductions', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('total_deductions', models.DecimalField(decimal_places=2, help_text='Total employee deductions', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('net_salary', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('status', models.CharField(choices=[('GENERATED', 'Generated'), ('PAID', 'Paid'), ('CANCELLED', 'Cancelled')], default='GENERATED', max_length=20)),
                ('payment_date', models.DateField(blank=True, help_text='Date when salary was paid', null=True)),
                ('remarks', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='salaries', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Salaries',
                'db_table': 'salaries',
                'ordering': ['-year', '-month'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='salary',
            unique_together={('employee', 'month', 'year')},
        ),
    ]
