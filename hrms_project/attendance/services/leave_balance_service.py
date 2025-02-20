from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from django.db.models import Q, QuerySet
from django.db import transaction
from calendar import monthrange
from decimal import Decimal

from attendance.models import LeaveBalance, LeaveType, Leave, Employee


class LeaveBalanceService:
    """Service for handling leave balance calculations"""

    @staticmethod
    def _calculate_leave_days(
        leave: Leave,
        start_date: date,
        end_date: date
    ) -> Decimal:
        """
        Calculate leave days for a specific period, handling half days.
        
        Args:
            leave: The leave record
            start_date: Period start date
            end_date: Period end date
            
        Returns:
            Decimal: Number of leave days
        """
        # For leaves spanning multiple months, only count days in current month
        leave_start = max(leave.start_date, start_date)
        leave_end = min(leave.end_date, end_date)
        days = Decimal(str((leave_end - leave_start).days + 1))
        
        # Adjust for half days
        if leave.start_half and leave_start == leave.start_date:
            days -= Decimal('0.5')
        if leave.end_half and leave_end == leave.end_date:
            days -= Decimal('0.5')
            
        return days

    @staticmethod
    def _get_period_dates(month: int, year: int) -> tuple[date, date]:
        """
        Get start and end dates for a given month/year.
        
        Args:
            month: Month number (1-12)
            year: Year
            
        Returns:
            tuple: (start_date, end_date)
        """
        start_date = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = date(year, month, last_day)
        return start_date, end_date

    @staticmethod
    def _process_balance_recalculation(
        employee: Employee,
        leave_type: LeaveType,
        start_date: date,
        end_date: date
    ) -> LeaveBalance:
        """
        Core balance recalculation logic.
        
        Args:
            employee: Employee to process
            leave_type: Leave type to process
            start_date: Period start date
            end_date: Period end date
            
        Returns:
            LeaveBalance: Updated balance record
        """
        # Calculate monthly allowance
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

        # Get approved leaves in period
        used_leaves = Leave.objects.filter(
            employee=employee,
            leave_type=leave_type,
            start_date__lte=end_date,
            end_date__gte=start_date,
            status='approved',
            is_active=True
        )

        # Calculate total days used
        total_used = sum(
            LeaveBalanceService._calculate_leave_days(leave, start_date, end_date)
            for leave in used_leaves
        )

        # Update balance
        balance.used_days = total_used
        balance.total_days = days_per_month
        balance.save()

        return balance

    @classmethod
    def recalculate_balances(
        cls,
        month: int,
        year: int,
        employees: Optional[QuerySet[Employee]] = None,
        leave_types: Optional[QuerySet[LeaveType]] = None
    ) -> List[LeaveBalance]:
        """
        Recalculate leave balances for specified employees and leave types.
        
        Args:
            month: Month to process
            year: Year to process
            employees: Optional queryset of employees to process (defaults to all active)
            leave_types: Optional queryset of leave types to process (defaults to all active)
            
        Returns:
            List of updated LeaveBalance records
        """
        # Get period dates
        start_date, end_date = cls._get_period_dates(month, year)
        
        # Get employees and leave types if not provided
        if employees is None:
            employees = Employee.objects.filter(is_active=True)
        if leave_types is None:
            leave_types = LeaveType.objects.filter(is_active=True)
        
        balances = []
        with transaction.atomic():
            for employee in employees:
                for leave_type in leave_types:
                    balance = cls._process_balance_recalculation(
                        employee=employee,
                        leave_type=leave_type,
                        start_date=start_date,
                        end_date=end_date
                    )
                    balances.append(balance)
        
        return balances

    @classmethod
    def recalculate_balance(
        cls,
        employee: Employee,
        leave_type: LeaveType,
        month: int,
        year: int
    ) -> LeaveBalance:
        """
        Recalculate leave balance for a specific employee and leave type.
        
        Args:
            employee: Employee to process
            leave_type: Leave type to process
            month: Month to process
            year: Year to process
            
        Returns:
            Updated LeaveBalance record
        """
        # Use the generic function with specific employee and leave type
        balances = cls.recalculate_balances(
            month=month,
            year=year,
            employees=Employee.objects.filter(pk=employee.pk),
            leave_types=LeaveType.objects.filter(pk=leave_type.pk)
        )
        return balances[0]

    @classmethod
    def recalculate_all_balances(cls, month: int, year: int) -> List[LeaveBalance]:
        """
        Recalculate leave balances for all active employees.
        
        Args:
            month: Month to process
            year: Year to process
            
        Returns:
            List of updated LeaveBalance records
        """
        # Use the generic function with default employee and leave type selection
        return cls.recalculate_balances(month=month, year=year)
