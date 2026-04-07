"""
Test script to verify payroll calculations match the payslip example
Example: Monthly CTC = 25000
Expected:
- Basic = 11738 (46.95% of 25000)
- HRA = 4695 (40% of basic)
- CA = 2347.5 (20% of basic)
- CCA = 1847.5 (13% of basic)
- Bonus = 2347.5 (20% of basic)
- Mobile = 500
- Gross = 23475
- Employee PF = 1409 (12% of basic)
- Employer PF = 1526 (13% of basic)
- Employee ESI = 0 (not applicable for salary > 21000)
- Employer ESI = 0 (not applicable for salary > 21000)
- Net = 22065 (Gross - Employee PF)
"""

from decimal import Decimal

# Test values
ctc_monthly = Decimal('25000')

# Calculate components
basic_salary = ctc_monthly * Decimal('0.4695')
hra = basic_salary * Decimal('0.40')
ca = basic_salary * Decimal('0.20')
cca = basic_salary * Decimal('0.1574')
bonus = basic_salary * Decimal('0.20')
mobile = Decimal('500')

# Calculate gross
gross_salary = basic_salary + hra + ca + cca + bonus + mobile

# Calculate deductions
pf_employee = basic_salary * Decimal('0.12')
pf_employer = basic_salary * Decimal('0.13')

# ESI (only if gross <= 21000)
if gross_salary <= Decimal('21000'):
    esi_employee = gross_salary * Decimal('0.0075')
    esi_employer = gross_salary * Decimal('0.0325')
else:
    esi_employee = Decimal('0.00')
    esi_employer = Decimal('0.00')

# Calculate net
net_salary = gross_salary - pf_employee - esi_employee

# Print results
print("=" * 60)
print("PAYROLL CALCULATION TEST")
print("=" * 60)
print(f"Monthly CTC: {ctc_monthly}")
print()
print("EARNINGS:")
print(f"  Basic Salary (46.95%): {basic_salary:.2f}")
print(f"  HRA (40% of basic): {hra:.2f}")
print(f"  CA (20% of basic): {ca:.2f}")
print(f"  CCA (13% of basic): {cca:.2f}")
print(f"  Bonus (20% of basic): {bonus:.2f}")
print(f"  Mobile: {mobile:.2f}")
print(f"  Gross Salary: {gross_salary:.2f}")
print()
print("DEDUCTIONS:")
print(f"  Employee PF (12% of basic): {pf_employee:.2f}")
print(f"  Employee ESI (0.75% of gross if applicable): {esi_employee:.2f}")
print(f"  Total Deductions: {pf_employee + esi_employee:.2f}")
print()
print("EMPLOYER CONTRIBUTIONS:")
print(f"  Employer PF (13% of basic): {pf_employer:.2f}")
print(f"  Employer ESI (3.25% of gross if applicable): {esi_employer:.2f}")
print()
print(f"Net Salary (Take-home): {net_salary:.2f}")
print()
print("=" * 60)
print("EXPECTED VALUES FROM PAYSLIP:")
print("=" * 60)
print("Basic: 11738")
print("HRA: 4695")
print("CA: 2347.5")
print("CCA: 1847.5")
print("Bonus: 2347.5")
print("Mobile: 500")
print("Gross: 23475")
print("Employee PF: 1409")
print("Employer PF: 1526")
print("Net: 22065")
print("=" * 60)
