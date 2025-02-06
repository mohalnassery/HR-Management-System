import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.db.models import F
from attendance.models import LeaveType, LeaveBalance, LeaveTransaction
from employees.models import Employee

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Reset leave balances for fixed-allowance leave types at the start of a new year'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            help='Specify year to reset balances for (defaults to current year)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate the reset without making actual changes'
        )

    def handle(self, *args, **options):
        year = options.get('year') or timezone.now().year
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('Running in dry-run mode - no changes will be made'))

        try:
            with transaction.atomic():
                # Get all active employees
                employees = Employee.objects.filter(is_active=True)
                self.stdout.write(f'Found {employees.count()} active employees')

                # Get leave types that need annual reset
                leave_types = LeaveType.objects.filter(
                    is_active=True,
                    rules__accrual_type='FIXED',
                    rules__reset_period='YEARLY'
                ).select_related('rules')

                self.stdout.write(f'Found {leave_types.count()} leave types to reset')

                balances_reset = 0
                balances_archived = 0

                for leave_type in leave_types:
                    self.stdout.write(f'\nProcessing {leave_type.name}:')
                    allowed_days = leave_type.rules.days_allowed

                    for employee in employees:
                        # Get current balance
                        try:
                            current_balance = LeaveBalance.objects.get(
                                employee=employee,
                                leave_type=leave_type
                            )

                            # Archive old balance if it exists and has transactions
                            if LeaveTransaction.objects.filter(
                                leave_balance=current_balance,
                                transaction_date__year=year-1
                            ).exists():
                                if not dry_run:
                                    LeaveBalance.objects.create(
                                        employee=employee,
                                        leave_type=leave_type,
                                        year=year-1,
                                        initial_balance=current_balance.initial_balance,
                                        current_balance=current_balance.current_balance,
                                        is_archived=True
                                    )
                                balances_archived += 1

                            # Reset balance to allowed days
                            if not dry_run:
                                current_balance.initial_balance = allowed_days
                                current_balance.current_balance = allowed_days
                                current_balance.year = year
                                current_balance.last_reset = timezone.now()
                                current_balance.save()

                                # Create reset transaction
                                LeaveTransaction.objects.create(
                                    leave_balance=current_balance,
                                    transaction_type='RESET',
                                    days=allowed_days,
                                    balance_after=allowed_days,
                                    description=f'Annual reset for {year}',
                                    transaction_date=timezone.now()
                                )
                            balances_reset += 1

                        except LeaveBalance.DoesNotExist:
                            # Create new balance if it doesn't exist
                            if not dry_run:
                                balance = LeaveBalance.objects.create(
                                    employee=employee,
                                    leave_type=leave_type,
                                    year=year,
                                    initial_balance=allowed_days,
                                    current_balance=allowed_days,
                                    last_reset=timezone.now()
                                )
                                LeaveTransaction.objects.create(
                                    leave_balance=balance,
                                    transaction_type='INITIAL',
                                    days=allowed_days,
                                    balance_after=allowed_days,
                                    description=f'Initial balance for {year}',
                                    transaction_date=timezone.now()
                                )
                            balances_reset += 1

                if not dry_run:
                    transaction.commit()
                    self.stdout.write(self.style.SUCCESS(
                        f'\nSuccessfully reset {balances_reset} balances and archived {balances_archived} old balances'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'\nDry run complete: Would reset {balances_reset} balances and archive {balances_archived} old balances'
                    ))

        except Exception as e:
            logger.error(f'Error resetting leave balances: {str(e)}')
            self.stdout.write(self.style.ERROR(f'Error resetting leave balances: {str(e)}'))
            if not dry_run:
                transaction.rollback()
            raise

    def _log_employee_balance(self, employee, leave_type, old_balance, new_balance):
        """Helper to log balance changes for auditing"""
        logger.info(
            f'Employee: {employee.employee_number} - {employee.get_full_name()}\n'
            f'Leave Type: {leave_type.name}\n'
            f'Old Balance: {old_balance}\n'
            f'New Balance: {new_balance}\n'
            f'Timestamp: {timezone.now()}\n'
            f'{"-"*50}'
        )
