from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from employees.models import Employee
from attendance.models import LeaveType
from attendance.services import LeaveBalanceService
import logging
from datetime import datetime, date
from calendar import monthrange
from decimal import Decimal

logger = logging.getLogger(__name__)

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
            employee_id = options.get('employee')
            leave_type_code = options.get('leave_type')

            # Validate month
            if not 1 <= month <= 12:
                raise CommandError('Month must be between 1 and 12')

            # Get employees to process
            employees = Employee.objects.filter(is_active=True)
            if employee_id:
                employees = employees.filter(id=employee_id)

            # Get leave types to process
            leave_types = LeaveType.objects.filter(is_active=True)
            if leave_type_code:
                leave_types = leave_types.filter(code=leave_type_code.upper())

            if not employees.exists():
                raise CommandError('No employees found')
            if not leave_types.exists():
                raise CommandError('No leave types found')

            self.stdout.write(
                self.style.SUCCESS(
                    f'Starting leave balance recalculation for {month:02d}/{year}'
                )
            )

            with transaction.atomic():
                for employee in employees:
                    self.stdout.write(
                        f'\nProcessing {employee.get_full_name()}:'
                    )

                    for leave_type in leave_types:
                        self.stdout.write(
                            f'  Leave Type: {leave_type.name}'
                        )

                        balance = LeaveBalanceService.recalculate_balance(
                            employee=employee,
                            leave_type=leave_type,
                            month=month,
                            year=year
                        )

                        # All fields are already Decimal from the model
                        available = balance.total_days - balance.used_days - balance.pending_days

                        self.stdout.write(
                            f'    Total Days: {float(balance.total_days):.2f}\n'
                            f'    Used Days: {float(balance.used_days):.2f}\n'
                            f'    Pending Days: {float(balance.pending_days):.2f}\n'
                            f'    Available Days: {float(available):.2f}'
                        )

            self.stdout.write(
                self.style.SUCCESS('Leave balances recalculated successfully')
            )
        except Exception as e:
            logger.error(f'Leave balance recalculation failed: {str(e)}', exc_info=True)
            raise CommandError(str(e))
