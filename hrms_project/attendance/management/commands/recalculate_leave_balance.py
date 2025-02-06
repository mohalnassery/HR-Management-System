from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q
from employees.models import Employee
from attendance.models import (
    AttendanceLog, Leave, LeaveType, LeaveBalance
)
from attendance.services import LeaveBalanceService
import logging
from datetime import datetime, date, timedelta
from calendar import monthrange

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Recalculate leave balances based on attendance records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date (YYYY-MM-DD)',
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date (YYYY-MM-DD)',
        )
        parser.add_argument(
            '--month',
            type=int,
            help='Month (1-12) - alternative to start/end dates',
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Year for processing',
        )
        parser.add_argument(
            '--employee',
            type=int,
            help='Employee ID to process',
        )
        parser.add_argument(
            '--leave-type',
            help='Leave type code to process (e.g., ANNUAL)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to see what would happen',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if balances exist',
        )

    def handle(self, *args, **options):
        # Process date range
        if options['month']:
            year = options['year'] or timezone.now().year
            month = options['month']
            _, last_day = monthrange(year, month)
            start_date = date(year, month, 1)
            end_date = date(year, month, last_day)
        else:
            try:
                start_date = datetime.strptime(options['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(options['end_date'], '%Y-%m-%d').date()
            except (TypeError, ValueError):
                raise CommandError('Invalid date format. Use YYYY-MM-DD')

        dry_run = options['dry_run']
        force = options['force']

        self.stdout.write(
            self.style.SUCCESS(
                f'Starting leave balance recalculation '
                f'({start_date} to {end_date})'
            )
        )

        try:
            with transaction.atomic():
                # Get employees to process
                employees = Employee.objects.filter(is_active=True)
                if options['employee']:
                    employees = employees.filter(id=options['employee'])

                # Get leave types to process
                leave_types = LeaveType.objects.filter(
                    is_active=True,
                    accrual_type='periodic'
                )
                if options['leave_type']:
                    leave_types = leave_types.filter(
                        code=options['leave_type'].upper()
                    )

                if not employees.exists():
                    raise CommandError('No employees found')
                if not leave_types.exists():
                    raise CommandError('No leave types found')

                for employee in employees:
                    self.stdout.write(
                        f'\nProcessing {employee.get_full_name()}:'
                    )

                    for leave_type in leave_types:
                        self.stdout.write(
                            f'  Leave Type: {leave_type.name}'
                        )

                        # Get attendance records
                        attendance_logs = AttendanceLog.objects.filter(
                            employee=employee,
                            date__range=(start_date, end_date),
                            is_active=True,
                            source__in=['system', 'manual', 'friday_rule']
                        ).exclude(
                            Q(status='leave') | Q(status='holiday')
                        )

                        # Calculate new accrual
                        worked_days = attendance_logs.filter(
                            Q(status='present') | 
                            (Q(source='friday_rule') & Q(status__in=['present', 'half']))
                        ).count()

                        accrual = (worked_days / leave_type.accrual_period) * leave_type.accrual_rate
                        current_period = f"{start_date.year}-{start_date.month:02d}"

                        # Get or create balance record
                        try:
                            balance = LeaveBalance.objects.get(
                                employee=employee,
                                leave_type=leave_type,
                                period=current_period,
                                is_active=True
                            )

                            if not force:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'    Balance already exists. '
                                        f'Use --force to update'
                                    )
                                )
                                continue

                        except LeaveBalance.DoesNotExist:
                            if not dry_run:
                                balance = LeaveBalance.objects.create(
                                    employee=employee,
                                    leave_type=leave_type,
                                    period=current_period,
                                    total_days=0,
                                    available_days=0
                                )

                        # Calculate leaves taken
                        leaves_taken = Leave.objects.filter(
                            employee=employee,
                            leave_type=leave_type,
                            start_date__gte=start_date,
                            end_date__lte=end_date,
                            status='approved',
                            is_active=True
                        ).aggregate(
                            total_days=models.Sum('duration')
                        )['total_days'] or 0

                        # Update balance
                        if not dry_run:
                            old_total = balance.total_days
                            old_available = balance.available_days
                            
                            balance.total_days = accrual
                            balance.available_days = max(0, accrual - leaves_taken)
                            balance.last_calculated = timezone.now()
                            balance.save()

                        self.stdout.write(
                            f'    Worked Days: {worked_days}\n'
                            f'    Accrual: {accrual:.2f}\n'
                            f'    Leaves Taken: {leaves_taken}\n'
                            f'    Old Balance: {old_total:.2f} '
                            f'({old_available:.2f} available)\n'
                            f'    New Balance: {accrual:.2f} '
                            f'({max(0, accrual - leaves_taken):.2f} available)'
                        )

                if dry_run:
                    transaction.set_rollback(True)
                    self.stdout.write(
                        self.style.SUCCESS('Dry run completed successfully')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('Leave balances recalculated successfully')
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error recalculating leave balances: {str(e)}')
            )
            logger.error(f'Leave balance recalculation failed: {str(e)}', exc_info=True)
            raise CommandError(str(e))
