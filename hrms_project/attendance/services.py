from django.utils import timezone
from django.db.models import Q, F
from datetime import datetime, timedelta, time
from typing import Optional, List, Dict, Any

from .models import (
    Employee, AttendanceLog, AttendanceRecord,
    Leave, LeaveType, LeaveBalance, Holiday
)

class FridayRuleService:
    """Service class for handling Friday attendance rules"""

    @staticmethod
    def get_friday_status(employee: Employee, friday_date: datetime.date) -> str:
        """
        Determine Friday attendance status based on Thursday and Saturday attendance.
        
        Rules:
        1. If employee works on both Thursday and Saturday -> Present
        2. If employee is absent on both Thursday and Saturday -> Absent
        3. If employee is present on either Thursday or Saturday -> Present
        """
        # Verify the date is a Friday
        if friday_date.weekday() != 4:  # 4 is Friday
            raise ValueError("Provided date is not a Friday")

        thursday_date = friday_date - timedelta(days=1)
        saturday_date = friday_date + timedelta(days=1)

        # Check Thursday attendance
        thursday_present = AttendanceLog.objects.filter(
            employee=employee,
            date=thursday_date,
            is_active=True,
            first_in_time__isnull=False
        ).exists()

        # Check Saturday attendance
        saturday_present = AttendanceLog.objects.filter(
            employee=employee,
            date=saturday_date,
            is_active=True,
            first_in_time__isnull=False
        ).exists()

        # Apply rules
        if thursday_present and saturday_present:
            return 'present'
        elif not thursday_present and not saturday_present:
            return 'absent'
        else:
            return 'present'

    @staticmethod
    def process_friday_attendance():
        """Process Friday attendance for all employees"""
        today = timezone.now().date()
        if today.weekday() != 4:  # Not Friday
            return

        employees = Employee.objects.filter(is_active=True)
        for employee in employees:
            status = FridayRuleService.get_friday_status(employee, today)
            AttendanceLog.objects.update_or_create(
                employee=employee,
                date=today,
                defaults={
                    'status': status,
                    'source': 'friday_rule'
                }
            )

class LeaveBalanceService:
    """Service class for managing leave balances"""

    @staticmethod
    def calculate_annual_leave_accrual(employee: Employee, period_start: datetime.date, period_end: datetime.date) -> float:
        """
        Calculate annual leave accrual based on worked days.
        Rate: 2.5 days for every 30 working days
        """
        # Count working days (including Fridays that count as worked)
        worked_days = AttendanceLog.objects.filter(
            Q(employee=employee) &
            Q(date__range=(period_start, period_end)) &
            Q(is_active=True) &
            (Q(status='present') | Q(source='friday_rule'))
        ).count()

        # Calculate accrual
        return (worked_days / 30) * 2.5

    @staticmethod
    def update_leave_balances():
        """Update leave balances for all employees"""
        today = timezone.now().date()
        first_of_month = today.replace(day=1)
        
        if today != first_of_month:  # Only run on first day of month
            return

        employees = Employee.objects.filter(is_active=True)
        leave_types = LeaveType.objects.filter(is_active=True)

        for employee in employees:
            for leave_type in leave_types:
                if leave_type.accrual_type == 'annual':
                    # Calculate accrual for previous month
                    last_month_end = first_of_month - timedelta(days=1)
                    last_month_start = last_month_end.replace(day=1)
                    
                    accrual = LeaveBalanceService.calculate_annual_leave_accrual(
                        employee, last_month_start, last_month_end
                    )

                    # Update balance
                    balance, created = LeaveBalance.objects.get_or_create(
                        employee=employee,
                        leave_type=leave_type,
                        is_active=True,
                        defaults={'total_days': 0, 'available_days': 0}
                    )
                    
                    balance.total_days += accrual
                    balance.available_days += accrual
                    balance.save()

class LeaveRequestService:
    """Service class for handling leave requests"""

    @staticmethod
    def validate_leave_request(
        employee: Employee,
        leave_type: LeaveType,
        start_date: datetime.date,
        end_date: datetime.date,
        start_half: bool = False,
        end_half: bool = False
    ) -> Dict[str, Any]:
        """Validate a leave request"""
        if start_date > end_date:
            return {'valid': False, 'error': 'End date cannot be before start date'}

        # Calculate duration
        duration = (end_date - start_date).days + 1
        if start_half:
            duration -= 0.5
        if end_half:
            duration -= 0.5

        # Check balance
        try:
            balance = LeaveBalance.objects.get(
                employee=employee,
                leave_type=leave_type,
                is_active=True
            )
            if duration > balance.available_days:
                return {
                    'valid': False,
                    'error': f'Insufficient leave balance. Available: {balance.available_days} days'
                }
        except LeaveBalance.DoesNotExist:
            return {'valid': False, 'error': 'No leave balance found'}

        # Check for overlapping leaves
        overlapping = Leave.objects.filter(
            employee=employee,
            is_active=True,
            status__in=['pending', 'approved'],
            start_date__lte=end_date,
            end_date__gte=start_date
        ).exists()

        if overlapping:
            return {'valid': False, 'error': 'Leave dates overlap with existing leave'}

        return {
            'valid': True,
            'duration': duration,
            'balance_after': balance.available_days - duration
        }

    @staticmethod
    def create_leave_request(
        employee: Employee,
        leave_type: LeaveType,
        start_date: datetime.date,
        end_date: datetime.date,
        reason: str,
        start_half: bool = False,
        end_half: bool = False,
        documents: List = None
    ) -> Dict[str, Any]:
        """Create a new leave request"""
        validation = LeaveRequestService.validate_leave_request(
            employee, leave_type, start_date, end_date, start_half, end_half
        )

        if not validation['valid']:
            return {'success': False, 'error': validation['error']}

        leave = Leave.objects.create(
            employee=employee,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            start_half=start_half,
            end_half=end_half,
            duration=validation['duration'],
            reason=reason,
            status='pending'
        )

        if documents:
            for doc in documents:
                leave.documents.create(document=doc)

        return {'success': True, 'leave_request': leave}

class RecurringHolidayService:
    """Service class for managing recurring holidays"""

    @staticmethod
    def generate_next_year_holidays():
        """Generate holidays for next year based on recurring holidays"""
        # Only run in December
        if timezone.now().month != 12:
            return

        next_year = timezone.now().year + 1
        holidays = Holiday.objects.filter(
            is_recurring=True,
            is_active=True
        )

        for holiday in holidays:
            # Create holiday for next year
            Holiday.objects.get_or_create(
                date=holiday.date.replace(year=next_year),
                defaults={
                    'name': holiday.name,
                    'holiday_type': holiday.holiday_type,
                    'description': holiday.description,
                    'is_paid': holiday.is_paid,
                    'is_recurring': False,  # New instance is not recurring
                }
            )
            
            if holiday.applicable_departments.exists():
                new_holiday = Holiday.objects.get(
                    date=holiday.date.replace(year=next_year)
                )
                new_holiday.applicable_departments.set(
                    holiday.applicable_departments.all()
                )
