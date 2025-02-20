from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.db.models import QuerySet
from employees.models import Employee
from attendance.models import LeaveType, LeaveBalance
from attendance.services import LeaveBalanceService
import logging
from datetime import datetime, date
from calendar import monthrange
from decimal import Decimal
from typing import Optional, List, TextIO, Tuple

logger = logging.getLogger(__name__)

class LeaveBalanceProcessor:
    """Handles leave balance processing operations"""
    
    @staticmethod
    def get_employees(employee_id: Optional[int] = None) -> QuerySet[Employee]:
        """
        Get employees to process based on filter criteria.
        
        Args:
            employee_id: Optional ID to filter specific employee
            
        Returns:
            QuerySet of employees
            
        Raises:
            CommandError: If no employees found
        """
        employees = Employee.objects.filter(is_active=True)
        if employee_id:
            employees = employees.filter(id=employee_id)
            
        if not employees.exists():
            raise CommandError('No employees found')
            
        return employees
    
    @staticmethod
    def get_leave_types(leave_type_code: Optional[str] = None) -> QuerySet[LeaveType]:
        """
        Get leave types to process based on filter criteria.
        
        Args:
            leave_type_code: Optional code to filter specific leave type
            
        Returns:
            QuerySet of leave types
            
        Raises:
            CommandError: If no leave types found
        """
        leave_types = LeaveType.objects.filter(is_active=True)
        if leave_type_code:
            leave_types = leave_types.filter(code=leave_type_code.upper())
            
        if not leave_types.exists():
            raise CommandError('No leave types found')
            
        return leave_types

class LeaveBalanceFormatter:
    """Handles formatting and output of leave balance information"""
    
    def __init__(self, stdout: TextIO):
        self.stdout = stdout
    
    def print_processing_start(self, month: int, year: int) -> None:
        """Print processing start message"""
        self.stdout.write(
            self.style_success(
                f'Starting leave balance recalculation for {month:02d}/{year}'
            )
        )
    
    def print_employee_header(self, employee: Employee) -> None:
        """Print employee processing header"""
        self.stdout.write(
            f'\nProcessing {employee.get_full_name()}:'
        )
    
    def print_leave_type_header(self, leave_type: LeaveType) -> None:
        """Print leave type processing header"""
        self.stdout.write(
            f'  Leave Type: {leave_type.name}'
        )
    
    def print_balance_details(self, balance: LeaveBalance) -> None:
        """
        Print formatted balance details.
        
        Args:
            balance: LeaveBalance instance to format and print
        """
        available = balance.total_days - balance.used_days - balance.pending_days
        
        self.stdout.write(
            f'    Total Days: {float(balance.total_days):.2f}\n'
            f'    Used Days: {float(balance.used_days):.2f}\n'
            f'    Pending Days: {float(balance.pending_days):.2f}\n'
            f'    Available Days: {float(available):.2f}'
        )
    
    def print_completion(self) -> None:
        """Print completion message"""
        self.stdout.write(
            self.style_success('Leave balances recalculated successfully')
        )
    
    @staticmethod
    def style_success(message: str) -> str:
        """Style success messages consistently"""
        return f'\033[92m{message}\033[0m'  # Green text

class Command(BaseCommand):
    help = 'Recalculate leave balances for a given month/year'

    def add_arguments(self, parser):
        parser.add_argument(
            '--month',
            type=int,
            required=True,
            help='Month to process (1-12)',
        )
        parser.add_argument(
            '--year',
            type=int,
            required=True,
            help='Year to process',
        )
        parser.add_argument(
            '--employee',
            type=int,
            help='Employee ID to process (optional)',
        )
        parser.add_argument(
            '--leave-type',
            help='Leave type code to process (optional)',
        )

    def handle(self, *args, **options):
        try:
            month = options['month']
            year = options['year']
            
            # Validate month
            if not 1 <= month <= 12:
                raise CommandError('Month must be between 1 and 12')
            
            # Initialize processors
            processor = LeaveBalanceProcessor()
            formatter = LeaveBalanceFormatter(self.stdout)
            
            # Get employees and leave types
            employees = processor.get_employees(options.get('employee'))
            leave_types = processor.get_leave_types(options.get('leave_type'))
            
            # Start processing
            formatter.print_processing_start(month, year)
            
            with transaction.atomic():
                for employee in employees:
                    formatter.print_employee_header(employee)
                    
                    for leave_type in leave_types:
                        formatter.print_leave_type_header(leave_type)
                        
                        # Calculate balance
                        balance = LeaveBalanceService.recalculate_balance(
                            employee=employee,
                            leave_type=leave_type,
                            month=month,
                            year=year
                        )
                        
                        # Print results
                        formatter.print_balance_details(balance)
            
            formatter.print_completion()
            
        except Exception as e:
            logger.error(f'Leave balance recalculation failed: {str(e)}', exc_info=True)
            raise CommandError(str(e))
