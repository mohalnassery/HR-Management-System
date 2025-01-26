from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from attendance.models import LeaveType, LeaveBalance
from employees.models import Employee
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Reset annual leave balances for all employees'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to see what would happen',
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Specify year to reset (defaults to current year)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        year = options['year'] or timezone.now().year

        self.stdout.write(
            self.style.SUCCESS(f'Starting annual leave reset for year {year}')
        )
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - no changes will be made')
            )

        try:
            with transaction.atomic():
                # Get all annual leave types
                leave_types = LeaveType.objects.filter(
                    is_active=True,
                    reset_period='yearly'
                )

                self.stdout.write(
                    f'Found {leave_types.count()} annual leave types'
                )

                # Process each leave type
                for leave_type in leave_types:
                    self.stdout.write(f'\nProcessing {leave_type.name}:')
                    
                    # Get all active employees
                    employees = Employee.objects.filter(is_active=True)
                    
                    for employee in employees:
                        try:
                            balance = LeaveBalance.objects.get(
                                employee=employee,
                                leave_type=leave_type,
                                is_active=True
                            )
                            
                            # Calculate carryover
                            old_balance = balance.available_days
                            if leave_type.allow_carryover:
                                carryover = min(
                                    old_balance,
                                    leave_type.max_carryover or old_balance
                                )
                            else:
                                carryover = 0
                            
                            new_balance = leave_type.default_days + carryover
                            
                            self.stdout.write(
                                f'  {employee.get_full_name()}: '
                                f'{old_balance} -> {new_balance} '
                                f'(Carryover: {carryover})'
                            )
                            
                            if not dry_run:
                                balance.total_days = new_balance
                                balance.available_days = new_balance
                                balance.save()
                                
                        except LeaveBalance.DoesNotExist:
                            # Create new balance if it doesn't exist
                            self.stdout.write(
                                f'  {employee.get_full_name()}: '
                                f'Creating new balance of {leave_type.default_days}'
                            )
                            
                            if not dry_run:
                                LeaveBalance.objects.create(
                                    employee=employee,
                                    leave_type=leave_type,
                                    total_days=leave_type.default_days,
                                    available_days=leave_type.default_days
                                )
                        
                        except Exception as e:
                            logger.error(
                                f'Error processing {employee.get_full_name()}: {str(e)}'
                            )
                            if not dry_run:
                                raise

                if dry_run:
                    transaction.set_rollback(True)
                    self.stdout.write(
                        self.style.SUCCESS('Dry run completed successfully')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('Leave balances reset successfully')
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error resetting leave balances: {str(e)}')
            )
            logger.error(f'Leave balance reset failed: {str(e)}')
            raise

    def format_balance(self, balance):
        """Format balance for display"""
        if balance % 1 == 0:
            return str(int(balance))
        return f"{balance:.1f}"
