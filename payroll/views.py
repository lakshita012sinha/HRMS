from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction, models
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal
from .models import SalaryStructure, Salary, EmployeeTDS
from .serializers import (
    SalaryStructureSerializer, SalarySerializer,
    GenerateSalarySerializer, MarkSalaryPaidSerializer, CTCSalaryStructureSerializer
)
from accounts.models import User


# ── Helper to get TDS for employee ───────────────────────────────────────────

def _get_employee_tds(employee, month, year):
    """
    Get TDS per month for an employee based on the given month/year.
    Returns Decimal('0.00') if no active TDS record found.
    """
    from datetime import date
    
    # Construct the target date (first day of the month)
    target_date = date(year, month, 1)
    
    # Get current financial year based on month/year
    if month >= 4:  # April onwards = current FY (e.g., 2026-27)
        fy_start_year = year
    else:  # Jan-Mar = belongs to previous FY
        fy_start_year = year - 1
    financial_year = f"{fy_start_year}-{str(fy_start_year + 1)[-2:]}"
    
    try:
        # Find active TDS record for this employee and financial year
        # where target_date is within the effective date range
        tds_record = EmployeeTDS.objects.filter(
            employee=employee,
            financial_year=financial_year,
            is_active=True,
            effective_date_from__lte=target_date
        ).filter(
            # Either effective_date_to is null (ongoing) OR target_date <= effective_date_to
            models.Q(effective_date_to__isnull=True) | models.Q(effective_date_to__gte=target_date)
        ).order_by('-effective_date_from').first()
        
        if tds_record:
            return Decimal(str(tds_record.tds_per_month))
    except Exception as e:
        print(f"Error fetching TDS for employee {employee.user_id}: {e}")
    
    return Decimal('0.00')


# ── Shared payroll calculation helper ─────────────────────────────────────────

def _compute_earned(ss, pay_days, total_days, tds_per_month=Decimal('0.00')):
    """
    Return a dict of all earned salary figures for a given pay_days / total_days ratio.

    Rules:
    - If pay_days == total_days  →  Earned = Entitled (exact copy, no rounding drift).
    - If pay_days <  total_days  →  Earned = Entitled × (pay_days / total_days), rounded to 2dp.
    - PF and ESI are re-derived from the *earned* basic / gross so the percentages
      remain correct after proration (not just prorated from the structure totals).
    - CTC = Gross + Employer PF + Employer ESI  (both contributions are inside CTC).
    - TDS is added to deductions if provided.
    - ESI is applicable only when monthly CTC ≤ ₹22,000
    """
    R = Decimal('0.01')
    D = Decimal

    pay_days   = D(str(pay_days))
    total_days = D(str(total_days))
    tds        = D(str(tds_per_month))
    full_month = pay_days >= total_days   # treat ≥ as full to handle rounding edge cases

    # ESI wage limit based on monthly CTC (not gross)
    esi_ctc_limit = D('22000.00')
    monthly_ctc = ss.ctc_monthly

    # Entitled (full-month) values from the salary structure
    entitled_gross = ss.calculate_gross_salary()   # Basic+HRA+CA+CCA+Bonus+Mobile

    if full_month:
        # Exact copy — no arithmetic drift
        basic  = ss.basic_salary
        hra    = ss.hra
        ca     = ss.ca
        cca    = ss.cca
        bonus  = ss.bonus
        mobile = ss.mobile
        gross  = entitled_gross
        other  = ss.other_deductions
    else:
        ratio  = pay_days / total_days
        basic  = (ss.basic_salary * ratio).quantize(R)
        hra    = (ss.hra          * ratio).quantize(R)
        ca     = (ss.ca           * ratio).quantize(R)
        cca    = (ss.cca          * ratio).quantize(R)
        bonus  = (ss.bonus        * ratio).quantize(R)
        mobile = (ss.mobile       * ratio).quantize(R)
        gross  = (basic + hra + ca + cca + bonus + mobile).quantize(R)
        other  = (ss.other_deductions * ratio).quantize(R)

    # PF — always 12% of earned basic
    pf_employee = (basic * D('0.12')).quantize(R)
    pf_employer = (basic * D('0.12')).quantize(R)

    # ESI — 0.75% / 3.25% of earned gross, only when monthly CTC ≤ ESI limit
    if monthly_ctc <= esi_ctc_limit:
        esi_employee = (gross * D('0.0075')).quantize(R)
        esi_employer = (gross * D('0.0325')).quantize(R)
    else:
        esi_employee = D('0.00')
        esi_employer = D('0.00')

    total_deductions = pf_employee + esi_employee + tds + other
    net_salary       = gross - total_deductions

    return {
        'basic_salary':    basic,
        'hra':             hra,
        'ca':              ca,
        'cca':             cca,
        'bonus':           bonus,
        'mobile':          mobile,
        'gross_salary':    gross,
        'pf_employee':     pf_employee,
        'pf_employer':     pf_employer,
        'esi_employee':    esi_employee,
        'esi_employer':    esi_employer,
        'tds':             tds,
        'other_deductions': other,
        'total_deductions': total_deductions,
        'net_salary':      net_salary,
    }


class CreateCTCSalaryStructureView(APIView):
    """Create CTC-based salary structure"""
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        # Only HR/Admin can create salary structure
        if not request.user.role or request.user.role.name not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR and Admin can create salary structures'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CTCSalaryStructureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        employee_id = serializer.validated_data['employee']
        ctc_monthly = serializer.validated_data['ctc_monthly']
        mobile = serializer.validated_data.get('mobile', 0)
        other_deductions = serializer.validated_data.get('other_deductions', 0)
        effective_from = serializer.validated_data['effective_from']
        
        # Get employee
        employee = User.objects.get(id=employee_id)
        
        # Check if employee already has active salary structure
        if SalaryStructure.objects.filter(employee=employee, is_active=True).exists():
            return Response(
                {'error': 'Active salary structure already exists for this employee'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create salary structure (calculations will be done in model's save method)
        salary_structure = SalaryStructure.objects.create(
            employee=employee,
            ctc_monthly=ctc_monthly,
            mobile=mobile,
            other_deductions=other_deductions,
            effective_from=effective_from,
            grade=serializer.validated_data.get('grade', ''),
            designation=serializer.validated_data.get('designation', ''),
        )
        
        return Response({
            'message': 'CTC-based salary structure created successfully',
            'salary_structure': SalaryStructureSerializer(salary_structure).data
        }, status=status.HTTP_201_CREATED)


# Salary Structure Management
class SalaryStructureListCreateView(generics.ListCreateAPIView):
    """List and create salary structures"""
    queryset = SalaryStructure.objects.filter(is_active=True)
    serializer_class = SalaryStructureSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = SalaryStructure.objects.filter(is_active=True)
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        elif user.role and user.role.name not in ['HR', 'ADMIN']:
            # Non-HR/Admin can only see their own salary structure
            queryset = queryset.filter(employee=user)
        
        return queryset.select_related('employee')
    
    def perform_create(self, serializer):
        # Only HR/Admin can create salary structure
        if not self.request.user.role or self.request.user.role.name not in ['HR', 'ADMIN']:
            raise permissions.PermissionDenied("Only HR and Admin can create salary structures")
        
        serializer.save()


class SalaryStructureDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete salary structure"""
    queryset = SalaryStructure.objects.all()
    serializer_class = SalaryStructureSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_update(self, serializer):
        # Only HR/Admin can update salary structure
        if not self.request.user.role or self.request.user.role.name not in ['HR', 'ADMIN']:
            raise permissions.PermissionDenied("Only HR and Admin can update salary structures")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        # Only HR/Admin can delete salary structure
        if not self.request.user.role or self.request.user.role.name not in ['HR', 'ADMIN']:
            raise permissions.PermissionDenied("Only HR and Admin can delete salary structures")
        
        # Soft delete
        instance.is_active = False
        instance.save()


class MySalaryStructureView(APIView):
    """Get current user's salary structure"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            salary_structure = SalaryStructure.objects.get(
                employee=request.user,
                is_active=True
            )
            serializer = SalaryStructureSerializer(salary_structure)
            return Response(serializer.data)
        except SalaryStructure.DoesNotExist:
            return Response(
                {'error': 'No salary structure found'},
                status=status.HTTP_404_NOT_FOUND
            )


# Salary Management
class SalaryListView(generics.ListAPIView):
    """List salary records"""
    serializer_class = SalarySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Salary.objects.all()
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        elif user.role and user.role.name not in ['HR', 'ADMIN']:
            # Non-HR/Admin can only see their own salary records
            queryset = queryset.filter(employee=user)
        
        # Filter by month and year
        month = self.request.query_params.get('month', None)
        year = self.request.query_params.get('year', None)
        if month:
            queryset = queryset.filter(month=month)
        if year:
            queryset = queryset.filter(year=year)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related('employee')


class SalaryDetailView(generics.RetrieveAPIView):
    """Retrieve salary record details"""
    queryset = Salary.objects.all()
    serializer_class = SalarySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Salary.objects.all()
        
        # Non-HR/Admin can only see their own salary records
        if user.role and user.role.name not in ['HR', 'ADMIN']:
            queryset = queryset.filter(employee=user)
        
        return queryset


class GenerateSalaryView(APIView):
    """Generate salary for an employee"""
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        # Only HR/Admin can generate salary
        if not request.user.role or request.user.role.name not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR and Admin can generate salary'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = GenerateSalarySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        employee_id = serializer.validated_data['employee']
        month = serializer.validated_data['month']
        year = serializer.validated_data['year']
        
        # Get employee
        employee = User.objects.get(id=employee_id)
        
        # Get salary structure
        try:
            salary_structure = SalaryStructure.objects.get(
                employee=employee,
                is_active=True
            )
        except SalaryStructure.DoesNotExist:
            return Response(
                {'error': 'No active salary structure found for this employee'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate salary components from salary structure
        # Use helper with full month (days_in_month = days_in_month → ratio=1.0)
        import calendar as cal
        days_in_month = cal.monthrange(year, month)[1]
        
        # Get TDS for this employee for this month/year
        tds_per_month = _get_employee_tds(employee, month, year)
        
        computed = _compute_earned(salary_structure, days_in_month, days_in_month, tds_per_month)

        # Create salary record
        salary = Salary.objects.create(
            employee=employee,
            month=month,
            year=year,
            ctc_monthly=salary_structure.ctc_monthly,
            basic_salary=computed['basic_salary'],
            hra=computed['hra'],
            ca=computed['ca'],
            cca=computed['cca'],
            bonus=computed['bonus'],
            mobile=computed['mobile'],
            gross_salary=computed['gross_salary'],
            pf_employee=computed['pf_employee'],
            pf_employer=computed['pf_employer'],
            esi_employee=computed['esi_employee'],
            esi_employer=computed['esi_employer'],
            tds=computed['tds'],
            other_deductions=computed['other_deductions'],
            total_deductions=computed['total_deductions'],
            net_salary=computed['net_salary'],
            status='GENERATED',
            paid_days=days_in_month,
        )
        
        return Response({
            'message': 'Salary generated successfully',
            'salary': SalarySerializer(salary).data
        }, status=status.HTTP_201_CREATED)


class MarkSalaryPaidView(APIView):
    """Mark salary as paid"""
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, pk):
        # Only HR/Admin can mark salary as paid
        if not request.user.role or request.user.role.name not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR and Admin can mark salary as paid'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            salary = Salary.objects.get(pk=pk)
        except Salary.DoesNotExist:
            return Response(
                {'error': 'Salary record not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if salary.status == 'PAID':
            return Response(
                {'error': 'Salary is already marked as paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if salary.status == 'CANCELLED':
            return Response(
                {'error': 'Cannot mark cancelled salary as paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = MarkSalaryPaidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        salary.status = 'PAID'
        salary.payment_date = serializer.validated_data['payment_date']
        salary.remarks = serializer.validated_data.get('remarks', '')
        salary.save()
        
        return Response({
            'message': 'Salary marked as paid successfully',
            'salary': SalarySerializer(salary).data
        }, status=status.HTTP_200_OK)


class CancelSalaryView(APIView):
    """Cancel salary record"""
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, pk):
        # Only HR/Admin can cancel salary
        if not request.user.role or request.user.role.name not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR and Admin can cancel salary'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            salary = Salary.objects.get(pk=pk)
        except Salary.DoesNotExist:
            return Response(
                {'error': 'Salary record not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if salary.status == 'PAID':
            return Response(
                {'error': 'Cannot cancel paid salary'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if salary.status == 'CANCELLED':
            return Response(
                {'error': 'Salary is already cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        salary.status = 'CANCELLED'
        salary.save()
        
        return Response({
            'message': 'Salary cancelled successfully',
            'salary': SalarySerializer(salary).data
        }, status=status.HTTP_200_OK)


class MySalaryView(APIView):
    """Get current user's salary records"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        year = request.query_params.get('year', datetime.now().year)
        month = request.query_params.get('month', None)
        
        queryset = Salary.objects.filter(employee=request.user, year=year)
        if month:
            queryset = queryset.filter(month=month)
        
        salaries = queryset.order_by('-year', '-month')
        serializer = SalarySerializer(salaries, many=True)
        return Response(serializer.data)


class GenerateMonthlyPayrollView(APIView):
    """
    Generate payroll for ALL employees for a given month based on attendance.
    
    Eligibility Check:
    - Employee must have minimum qualifying worked days (from PayrollSettings)
    - Qualifying worked days = PRESENT + HALF_DAY attendance (excludes Sundays/weekly-offs)
    - If worked_days < minimum → NOT_ELIGIBLE (no payroll/payslip generated)
    - If worked_days >= minimum → ELIGIBLE (payroll generated)
    
    Payable Days Calculation (for eligible employees):
    - pay_days = present + sundays + paid_leave_days
    - Used for salary proration
    
    Note: Eligibility uses worked days only. Payable days includes Sundays for calculation.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        if not request.user.role or request.user.role.name not in ['HR', 'ADMIN']:
            return Response({'error': 'Only HR and Admin can generate payroll'}, status=status.HTTP_403_FORBIDDEN)

        month = request.data.get('month')
        year  = request.data.get('year')
        if not month or not year:
            return Response({'error': 'month and year are required'}, status=status.HTTP_400_BAD_REQUEST)

        month = int(month)
        year  = int(year)

        import calendar as cal
        from attendance.models import Attendance, Holiday
        from datetime import date, timedelta
        from .models import PayrollSettings

        # Get minimum days setting
        payroll_settings = PayrollSettings.get_settings()
        minimum_required_days = payroll_settings.minimum_days_for_payroll

        days_in_month = cal.monthrange(year, month)[1]

        # Count sundays in the month
        sundays = sum(1 for d in range(1, days_in_month + 1) if date(year, month, d).weekday() == 6)

        # Holidays
        holidays = set(Holiday.objects.filter(date__year=year, date__month=month).values_list('date', flat=True))
        holiday_count = len(holidays)

        # All attendance records for this month
        att_qs = Attendance.objects.filter(date__year=year, date__month=month).select_related('employee')
        att_map = {}  # employee_id -> {present, half_day}
        for a in att_qs:
            emp_id = a.employee_id
            if emp_id not in att_map:
                att_map[emp_id] = {'present': 0, 'half_day': 0}
            if a.status == 'PRESENT':
                att_map[emp_id]['present'] += 1
            elif a.status == 'HALF_DAY':
                att_map[emp_id]['half_day'] += 1

        # Get all approved leave requests of the month
        from leave_management.models import LeaveRequest
        approved_leaves = LeaveRequest.objects.filter(
            status='APPROVED',
            start_date__lte=date(year, month, days_in_month),
            end_date__gte=date(year, month, 1)
        ).select_related('leave_type')

        # Build a map of employee -> set of paid leave dates in this month
        paid_leave_map = {}
        for lr in approved_leaves:
            if not lr.leave_type.is_paid:
                continue
            if lr.employee_id not in paid_leave_map:
                paid_leave_map[lr.employee_id] = set()
            
            # Add all dates in the range that fall within this month
            cur = max(lr.start_date, date(year, month, 1))
            last = min(lr.end_date, date(year, month, days_in_month))
            while cur <= last:
                paid_leave_map[lr.employee_id].add(cur)
                cur += timedelta(days=1)

        generated = []
        skipped   = []
        not_eligible = []

        employees = User.objects.filter(is_active=True).exclude(role__name__in=['ADMIN'])
        for emp in employees:
            # Must have salary structure
            try:
                ss = SalaryStructure.objects.get(employee=emp, is_active=True)
            except SalaryStructure.DoesNotExist:
                skipped.append({'employee': emp.user_id, 'reason': 'No salary structure'})
                continue

            # Skip if already generated
            if Salary.objects.filter(employee=emp, month=month, year=year).exists():
                skipped.append({'employee': emp.user_id, 'reason': 'Salary already generated'})
                continue

            # Calculate qualifying worked days (PRESENT + HALF_DAY, excludes Sundays)
            emp_att = att_map.get(emp.id, {'present': 0, 'half_day': 0})
            worked_days = emp_att['present'] + emp_att['half_day'] * Decimal('0.5')
            
            # Check eligibility based on qualifying worked days
            is_eligible = worked_days >= minimum_required_days
            
            if not is_eligible:
                # Create NOT_ELIGIBLE salary record (for tracking purposes)
                reason = f"Minimum qualifying worked days not met. Worked: {worked_days}, Required: {minimum_required_days}"
                sal = Salary.objects.create(
                    employee=emp,
                    month=month, year=year,
                    worked_days=float(worked_days),
                    minimum_required_days=minimum_required_days,
                    is_eligible=False,
                    ineligibility_reason=reason,
                    ctc_monthly=ss.ctc_monthly,
                    basic_salary=Decimal('0.00'),
                    hra=Decimal('0.00'),
                    ca=Decimal('0.00'),
                    cca=Decimal('0.00'),
                    bonus=Decimal('0.00'),
                    mobile=Decimal('0.00'),
                    gross_salary=Decimal('0.00'),
                    pf_employee=Decimal('0.00'),
                    pf_employer=Decimal('0.00'),
                    esi_employee=Decimal('0.00'),
                    esi_employer=Decimal('0.00'),
                    tds=Decimal('0.00'),
                    other_deductions=Decimal('0.00'),
                    total_deductions=Decimal('0.00'),
                    net_salary=Decimal('0.00'),
                    status='NOT_ELIGIBLE',
                    paid_days=0,
                    remarks=reason
                )
                not_eligible.append({
                    'employee': emp.user_id,
                    'name': f"{emp.first_name} {emp.last_name}".strip(),
                    'worked_days': float(worked_days),
                    'required_days': minimum_required_days,
                    'reason': reason
                })
                continue

            # Employee is ELIGIBLE - calculate payable days for salary calculation
            present = emp_att['present'] + emp_att['half_day'] * Decimal('0.5')
            
            # Count paid leave days (excluding Sundays and actual worked days to avoid double counting)
            worked_dates = set(a.date for a in att_qs if a.employee_id == emp.id and a.status in ['PRESENT', 'HALF_DAY'])
            paid_leave_days = 0
            for dt in paid_leave_map.get(emp.id, set()):
                if dt.weekday() != 6 and dt not in worked_dates:
                    paid_leave_days += 1
            
            # Payable days = present + sundays + paid leaves (used for salary calculation)
            pay_days = present + sundays + paid_leave_days

            # Cap at days_in_month
            pay_days = min(pay_days, days_in_month)

            # Get TDS for this employee for this month/year
            tds_per_month = _get_employee_tds(emp, month, year)

            # Compute earned salary (full-month if pay_days==days_in_month, prorated otherwise)
            computed = _compute_earned(ss, float(pay_days), days_in_month, tds_per_month)

            sal = Salary.objects.create(
                employee=emp,
                month=month, year=year,
                worked_days=float(worked_days),
                minimum_required_days=minimum_required_days,
                is_eligible=True,
                ineligibility_reason='',
                ctc_monthly=ss.ctc_monthly,
                basic_salary=computed['basic_salary'],
                hra=computed['hra'],
                ca=computed['ca'],
                cca=computed['cca'],
                bonus=computed['bonus'],
                mobile=computed['mobile'],
                gross_salary=computed['gross_salary'],
                pf_employee=computed['pf_employee'],
                pf_employer=computed['pf_employer'],
                esi_employee=computed['esi_employee'],
                esi_employer=computed['esi_employer'],
                tds=computed['tds'],
                other_deductions=computed['other_deductions'],
                total_deductions=computed['total_deductions'],
                net_salary=computed['net_salary'],
                status='GENERATED',
                paid_days=float(pay_days),
                remarks=f'Worked: {worked_days} days, Payable: {pay_days}/{days_in_month} (Present:{present} + Sundays:{sundays} + PaidLeave:{paid_leave_days})'
            )
            generated.append({
                'employee': emp.user_id,
                'name': f"{emp.first_name} {emp.last_name}".strip(),
                'worked_days': float(worked_days),
                'pay_days': float(pay_days),
                'net_salary': float(sal.net_salary),
            })

        return Response({
            'message': f'Payroll processed for {len(employees)} employees.',
            'month': month, 'year': year,
            'minimum_required_days': minimum_required_days,
            'summary': {
                'eligible_generated': len(generated),
                'not_eligible': len(not_eligible),
                'skipped': len(skipped)
            },
            'generated': generated,
            'not_eligible': not_eligible,
            'skipped': skipped,
        }, status=status.HTTP_201_CREATED)


class SalaryGradeListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        from .serializers import SalaryGradeSerializer
        return SalaryGradeSerializer

    def get_queryset(self):
        from .models import SalaryGrade
        return SalaryGrade.objects.all()


class SalaryGradeDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        from .serializers import SalaryGradeSerializer
        return SalaryGradeSerializer

    def get_queryset(self):
        from .models import SalaryGrade
        return SalaryGrade.objects.all()


# ── TDS Management ────────────────────────────────────────────────────────────

class EmployeeTDSListCreateView(generics.ListCreateAPIView):
    """List and create TDS records"""
    from .models import EmployeeTDS
    from .serializers import EmployeeTDSSerializer
    
    queryset = EmployeeTDS.objects.filter(is_active=True)
    serializer_class = EmployeeTDSSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter TDS records by employee if 'employee' query param is provided"""
        queryset = super().get_queryset()
        employee_code = self.request.query_params.get('employee', None)
        
        if employee_code:
            try:
                employee = User.objects.get(user_id=employee_code)
                queryset = queryset.filter(employee=employee)
            except User.DoesNotExist:
                queryset = queryset.none()
        
        return queryset.order_by('-financial_year', '-effective_date_from')


class EmployeeTDSDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete TDS record"""
    from .models import EmployeeTDS
    from .serializers import EmployeeTDSSerializer
    
    queryset = EmployeeTDS.objects.all()
    serializer_class = EmployeeTDSSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        """Soft delete by setting is_active to False"""
        instance.is_active = False
        instance.save()
