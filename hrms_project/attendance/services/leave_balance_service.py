from datetime import datetime, date
from django.db.models import Q
from django.db import transaction
from calendar import monthrange
from decimal import Decimal

from attendance.models import LeaveBalance, LeaveType, Leave, Employee


class LeaveBalanceService:
    @staticmethod
    def recalculate_balance(employee, leave_type, month, year):
        """
        Recalculate leave balance for a specific employee, leave type and month/year
        """
        # Calculate monthly allowance based on yearly days
        days_per_month = Decimal(str(leave_type.days_allowed)) / Decimal('12')
        
        # Get or create leave balance
        balance, created = LeaveBalance.objects.get_or_create(
            employee=employee,
            leave_type=leave_type,
            defaults={
                'total_days': days_per_month,
                'used_days': Decimal('0'),
                'pending_days': Decimal('0')
            }
        )

        # Calculate used leaves in this month
        start_date = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = date(year, month, last_day)

        used_leaves = Leave.objects.filter(
            employee=employee,
            leave_type=leave_type,
            start_date__lte=end_date,
            end_date__gte=start_date,
            status='approved',
            is_active=True
        )

        # Calculate total days used
        total_used = Decimal('0')
        for leave in used_leaves:
            # For leaves spanning multiple months, only count days in current month
            leave_start = max(leave.start_date, start_date)
            leave_end = min(leave.end_date, end_date)
            days = Decimal(str((leave_end - leave_start).days + 1))
            
            # Adjust for half days
            if leave.start_half and leave_start == leave.start_date:
                days -= Decimal('0.5')
            if leave.end_half and leave_end == leave.end_date:
                days -= Decimal('0.5')
                
            total_used += days

        # Update balance
        balance.used_days = total_used
        balance.total_days = days_per_month
        balance.save()

        return balance

    @staticmethod
    def recalculate_all_balances(month, year):
        """
        Recalculate leave balances for all active employees for given month/year
        """
        employees = Employee.objects.filter(is_active=True)
        leave_types = LeaveType.objects.filter(is_active=True)
        
        balances = []
        with transaction.atomic():
            for employee in employees:
                for leave_type in leave_types:
                    balance = LeaveBalanceService.recalculate_balance(
                        employee=employee,
                        leave_type=leave_type,
                        month=month,
                        year=year
                    )
                    balances.append(balance)
        
        return balances
