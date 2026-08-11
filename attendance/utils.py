"""
Attendance utility functions including Sunday Sandwich Rule implementation.

Sunday Sandwich Rule:
- If an employee has ABSENCE or UNAPPROVED LEAVE on both Saturday AND Monday,
  Sunday (weekly off) is counted as ABSENT/LEAVE instead of weekly off.
- If the leave on Saturday and/or Monday is APPROVED, Sunday remains a weekly off.
- One-sided patterns (leave only before or only after Sunday) do NOT trigger the rule.
"""

from datetime import timedelta
from attendance.models import Attendance
from leave_management.models import LeaveRequest


def is_sunday_sandwiched(employee, sunday_date):
    """
    Check if a Sunday is sandwiched between unapproved leave/absence.
    
    Args:
        employee: User object
        sunday_date: date object representing a Sunday
        
    Returns:
        dict with:
            - is_sandwiched (bool): True if sandwich rule applies
            - reason (str): Explanation of the decision
            - saturday_status (str): Status of Saturday
            - monday_status (str): Status of Monday
    """
    # Verify it's actually a Sunday
    if sunday_date.weekday() != 6:
        return {
            'is_sandwiched': False,
            'reason': 'Not a Sunday',
            'saturday_status': None,
            'monday_status': None
        }
    
    saturday = sunday_date - timedelta(days=1)
    monday = sunday_date + timedelta(days=1)
    
    # Get attendance records for Saturday and Monday
    saturday_att = Attendance.objects.filter(employee=employee, date=saturday).first()
    monday_att = Attendance.objects.filter(employee=employee, date=monday).first()
    
    saturday_status = saturday_att.status if saturday_att else None
    monday_status = monday_att.status if monday_att else None
    
    # Check if both Saturday and Monday have leave/absence
    saturday_is_leave_or_absent = saturday_status in ['ABSENT', 'LEAVE']
    monday_is_leave_or_absent = monday_status in ['ABSENT', 'LEAVE']
    
    # If either day is not leave/absent, no sandwich
    if not (saturday_is_leave_or_absent and monday_is_leave_or_absent):
        return {
            'is_sandwiched': False,
            'reason': 'Not surrounded by leave/absence on both sides',
            'saturday_status': saturday_status,
            'monday_status': monday_status
        }
    
    # Both are leave/absent - now check if they are APPROVED leaves
    saturday_has_approved_leave = _has_approved_leave(employee, saturday)
    monday_has_approved_leave = _has_approved_leave(employee, monday)
    
    # If BOTH Saturday and Monday have APPROVED leave, Sunday remains weekly off
    if saturday_has_approved_leave and monday_has_approved_leave:
        return {
            'is_sandwiched': False,
            'reason': 'Surrounded by approved leaves - Sunday remains weekly off',
            'saturday_status': saturday_status,
            'monday_status': monday_status,
            'saturday_approved': True,
            'monday_approved': True
        }
    
    # At least one side has unapproved leave/absence - apply sandwich rule
    return {
        'is_sandwiched': True,
        'reason': 'Surrounded by unapproved leave/absence - Sunday counted as absent',
        'saturday_status': saturday_status,
        'monday_status': monday_status,
        'saturday_approved': saturday_has_approved_leave,
        'monday_approved': monday_has_approved_leave
    }


def _has_approved_leave(employee, date):
    """
    Check if employee has an APPROVED leave on the given date.
    
    Args:
        employee: User object
        date: date object
        
    Returns:
        bool: True if there's an approved leave covering this date
    """
    approved_leaves = LeaveRequest.objects.filter(
        employee=employee,
        status='APPROVED',
        start_date__lte=date,
        end_date__gte=date
    )
    return approved_leaves.exists()


def get_sandwiched_sundays_in_month(employee, year, month):
    """
    Get all Sundays in a month that are sandwiched by unapproved leave/absence.
    
    Args:
        employee: User object
        year: int
        month: int
        
    Returns:
        list of dicts with date and sandwich info for each sandwiched Sunday
    """
    from datetime import date
    import calendar
    
    days_in_month = calendar.monthrange(year, month)[1]
    sandwiched_sundays = []
    
    for day in range(1, days_in_month + 1):
        dt = date(year, month, day)
        if dt.weekday() == 6:  # Sunday
            sandwich_info = is_sunday_sandwiched(employee, dt)
            if sandwich_info['is_sandwiched']:
                sandwiched_sundays.append({
                    'date': dt,
                    'info': sandwich_info
                })
    
    return sandwiched_sundays


def count_sandwiched_sundays(employee, year, month):
    """
    Count the number of sandwiched Sundays in a month for an employee.
    
    Args:
        employee: User object
        year: int
        month: int
        
    Returns:
        int: Number of sandwiched Sundays
    """
    return len(get_sandwiched_sundays_in_month(employee, year, month))


def apply_sunday_sandwich_rule_to_attendance(employee, year, month):
    """
    Apply Sunday Sandwich Rule to attendance records for a given month.
    This should be called after attendance is marked/updated.
    
    Updates Sunday attendance records to 'ABSENT' if sandwiched by unapproved leave/absence.
    
    Args:
        employee: User object
        year: int
        month: int
        
    Returns:
        dict with:
            - updated_count: Number of Sundays updated
            - updated_dates: List of Sunday dates that were updated
    """
    sandwiched = get_sandwiched_sundays_in_month(employee, year, month)
    updated_dates = []
    
    for item in sandwiched:
        sunday_date = item['date']
        # Get or create attendance for this Sunday
        att, created = Attendance.objects.get_or_create(
            employee=employee,
            date=sunday_date,
            defaults={'status': 'ABSENT', 'remarks': 'Sunday Sandwich Rule applied'}
        )
        
        # Update to ABSENT if it was WEEKEND
        if att.status in ['WEEKEND', 'HOLIDAY']:
            att.status = 'ABSENT'
            att.remarks = f'Sunday Sandwich Rule: Surrounded by unapproved leave/absence. {att.remarks}'.strip()
            att.save()
            updated_dates.append(sunday_date)
    
    return {
        'updated_count': len(updated_dates),
        'updated_dates': updated_dates
    }
