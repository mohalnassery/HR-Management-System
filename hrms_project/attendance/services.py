from django.utils import timezone
from django.db.models import Q, F
from datetime import datetime, timedelta, time
from typing import Optional, List, Dict, Any

from .models import (
    Employee, AttendanceLog, AttendanceRecord,
    Leave, LeaveType, LeaveBalance, Holiday,
    ShiftAssignment, RamadanPeriod
)

class AttendanceStatusService:
    """Service class for determining attendance status"""

    @staticmethod
    def is_ramadan(date: datetime.date, employee: Employee) -> bool:
        """Check if the given date falls within Ramadan period for Muslim employees"""
        if employee.religion != "Muslim":
            return False

        return RamadanPeriod.objects.filter(
            year=date.year,
            start_date__lte=date,
            end_date__gte=date,
            is_active=True
        ).exists()

    @staticmethod
    def get_employee_shift(employee: Employee, date: datetime.date) -> Optional[ShiftAssignment]:
        """Get the active shift assignment for an employee on a given date"""
        return ShiftAssignment.objects.filter(
            employee=employee,
            start_date__lte=date,
            is_active=True
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=date)
        ).first()

    
    @staticmethod
    def calculate_status(attendance_log: AttendanceLog) -> dict:
        """
        Calculate attendance status, late minutes, early departure etc.
        Returns dict with status details
        """
        # Get the shift assignment
        shift_assignment = AttendanceStatusService.get_employee_shift(
            attendance_log.employee, attendance_log.date
        )

        # If no shift assigned, use default shift
        if not shift_assignment:
            shift = attendance_log.shift  # Fallback to the one set in attendance_log
            if not shift:
                return {
                    'status': 'absent',
                    'is_late': False,
                    'late_minutes': 0,
                    'early_departure': False,
                    'early_minutes': 0,
                    'total_work_minutes': 0
                }
        else:
            shift = shift_assignment.shift
            attendance_log.shift = shift  # Update the log with the correct shift

        
        # Check if it's Ramadan for Muslim employees
        is_ramadan_day = AttendanceStatusService.is_ramadan(attendance_log.date, attendance_log.employee)

        # Get shift times
        shift_start = shift.start_time
        shift_end = shift.end_time if not is_ramadan_day else (
            datetime.combine(attendance_log.date, shift_start) + timedelta(hours=6)
        ).time()
        
        # Initialize result
        result = {
            'status': 'absent',
            'is_late': False,
            'late_minutes': 0,
            'early_departure': False,
            'early_minutes': 0,
            'total_work_minutes': 0
        }
        
        # If no check-in/out, mark as absent
        if not attendance_log.first_in_time or not attendance_log.last_out_time:
            return result

        # Apply grace period for lateness
        actual_start = (
            datetime.combine(attendance_log.date, shift_start) + 
            timedelta(minutes=shift.grace_period)
        ).time()

        # Calculate late minutes only if beyond grace period
        if attendance_log.first_in_time > actual_start:
            late_delta = datetime.combine(attendance_log.date, attendance_log.first_in_time) - \
                        datetime.combine(attendance_log.date, shift_start)
            result['is_late'] = True
            result['late_minutes'] = late_delta.seconds // 60
            
        # Calculate early departure
        if attendance_log.last_out_time < shift_end:
            early_delta = datetime.combine(attendance_log.date, shift_end) - \
                         datetime.combine(attendance_log.date, attendance_log.last_out_time)
            result['early_departure'] = True
            result['early_minutes'] = early_delta.seconds // 60
            
        # Calculate total work minutes
        work_delta = datetime.combine(attendance_log.date, attendance_log.last_out_time) - \
                    datetime.combine(attendance_log.date, attendance_log.first_in_time)

        total_minutes = work_delta.seconds // 60

        # Handle break deduction
        if is_ramadan_day:
            # No break deduction during Ramadan
            result['total_work_minutes'] = total_minutes
        else:
            # Always deduct break duration unless it's a custom shift with different break duration
            result['total_work_minutes'] = total_minutes - shift.break_duration
        
        # Determine status
        if result['is_late']:
            result['status'] = 'late'
        else:
            result['status'] = 'present'
            
        return result
    
    @staticmethod
    def update_attendance_status(attendance_log: AttendanceLog):
        """Update attendance log with calculated status"""
        status_details = AttendanceStatusService.calculate_status(attendance_log)
        
        for key, value in status_details.items():
            setattr(attendance_log, key, value)
            
        attendance_log.save()


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
                if leave_type.accrual_enabled and leave_type.accrual_period == 'WORKED':
                    # Calculate accrual for previous month
                    last_month_end = first_of_month - timedelta(days=1)
                    last_month_start = last_month_end.replace(day=1)
                    
                    try:
                        # Calculate accrual
                        accrual = LeaveBalanceService.calculate_annual_leave_accrual(
                            employee, last_month_start, last_month_end
                        )

                        # Update balance
                        balance, created = LeaveBalance.objects.get_or_create(
                            employee=employee,
                            leave_type=leave_type,
                            is_active=True,
                            defaults={'total_days': 0}
                        )
                        
                        # Update last accrual date
                        balance.last_accrual_date = last_month_end
                        balance.total_days += accrual
                        balance.save()
                    except Exception as e:
                        print(f"Error updating leave balance for {employee} - {leave_type}: {str(e)}")
                        continue

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
        """Generate next year's holidays from recurring holidays"""
        current_year = timezone.now().year
        next_year = current_year + 1
        
        recurring_holidays = Holiday.objects.filter(is_recurring=True)
        
        for holiday in recurring_holidays:
            # Create new holiday instance for next year
            new_date = holiday.date.replace(year=next_year)
            Holiday.objects.create(
                name=holiday.name,
                date=new_date,
                holiday_type=holiday.holiday_type,
                description=holiday.description,
                is_paid=holiday.is_paid,
                is_recurring=False  # New instance is not recurring
            )

class RamadanService:
    """Service class for handling Ramadan-specific logic"""

    @staticmethod
    def get_ramadan_shift_timing(shift, date):
        """
        Get Ramadan-adjusted shift timing if applicable
        Returns dict with start_time and end_time
        """
        if not shift:
            return {}

        # Check if date falls in Ramadan period
        ramadan_period = RamadanPeriod.objects.filter(
            year=date.year,
            start_date__lte=date,
            end_date__gte=date,
            is_active=True
        ).first()

        if not ramadan_period:
            return {}

        # Use Ramadan specific times if set, otherwise use default times
        start_time = shift.ramadan_start_time or shift.start_time
        end_time = shift.ramadan_end_time or shift.end_time

        return {
            'start_time': start_time,
            'end_time': end_time
        }

class HolidayService:
    @staticmethod
    def generate_next_year_holidays():
        """Generate next year's holidays from recurring holidays"""
        current_year = timezone.now().year
        next_year = current_year + 1
        
        recurring_holidays = Holiday.objects.filter(is_recurring=True)
        
        for holiday in recurring_holidays:
            # Create new holiday instance for next year
            new_date = holiday.date.replace(year=next_year)
            Holiday.objects.create(
                name=holiday.name,
                date=new_date,
                holiday_type=holiday.holiday_type,
                description=holiday.description,
                is_paid=holiday.is_paid,
                is_recurring=False  # New instance is not recurring
            )
