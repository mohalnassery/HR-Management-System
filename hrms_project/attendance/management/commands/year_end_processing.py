from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.core.management import call_command
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Perform end-of-year processing tasks for attendance management'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            help='Year to process (defaults to current year)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to see what would happen',
        )
        parser.add_argument(
            '--skip-reset',
            action='store_true',
            help='Skip leave balance reset',
        )
        parser.add_argument(
            '--skip-holidays',
            action='store_true',
            help='Skip holiday generation',
        )
        parser.add_argument(
            '--skip-archive',
            action='store_true',
            help='Skip record archiving',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force processing even if not December',
        )

    def handle(self, *args, **options):
        year = options['year'] or timezone.now().year
        dry_run = options['dry_run']
        skip_reset = options['skip_reset']
        skip_holidays = options['skip_holidays']
        skip_archive = options['skip_archive']
        force = options['force']

        # Check if it's December or force flag is set
        if timezone.now().month != 12 and not force:
            self.stdout.write(
                self.style.WARNING(
                    'Year-end processing should be run in December. '
                    'Use --force to override.'
                )
            )
            return

        try:
            with transaction.atomic():
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Starting year-end processing for {year}'
                    )
                )

                if not skip_reset:
                    self.stdout.write('Resetting leave balances...')
                    try:
                        if not dry_run:
                            call_command('reset_annual_leave', year=year + 1)
                        self.stdout.write('Leave balances reset complete')
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Error resetting leave balances: {str(e)}')
                        )
                        raise

                if not skip_holidays:
                    self.stdout.write('Generating holidays for next year...')
                    try:
                        if not dry_run:
                            call_command('generate_holidays', year=year + 1, force=True)
                        self.stdout.write('Holiday generation complete')
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Error generating holidays: {str(e)}')
                        )
                        raise

                if not skip_archive:
                    self.stdout.write('Archiving old records...')
                    try:
                        if not dry_run:
                            self._archive_old_records(year)
                        self.stdout.write('Record archiving complete')
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Error archiving records: {str(e)}')
                        )
                        raise

                # Generate year-end reports
                self.stdout.write('Generating year-end reports...')
                try:
                    if not dry_run:
                        self._generate_year_end_reports(year)
                    self.stdout.write('Report generation complete')
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error generating reports: {str(e)}')
                    )
                    raise

                if dry_run:
                    transaction.set_rollback(True)
                    self.stdout.write(
                        self.style.SUCCESS('Dry run completed successfully')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('Year-end processing completed successfully')
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Year-end processing failed: {str(e)}')
            )
            logger.error(f'Year-end processing failed: {str(e)}', exc_info=True)
            raise CommandError(str(e))

    def _archive_old_records(self, year):
        """Archive old attendance records and logs"""
        from attendance.models import (
            AttendanceRecord, AttendanceLog, Leave, 
            LeaveBalance, Holiday
        )
        
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)

        # Archive attendance records
        AttendanceRecord.objects.filter(
            timestamp__year=year,
            is_active=True
        ).update(
            is_active=False,
            archived_at=timezone.now()
        )

        # Archive attendance logs
        AttendanceLog.objects.filter(
            date__year=year,
            is_active=True
        ).update(
            is_active=False,
            archived_at=timezone.now()
        )

        # Archive completed leaves
        Leave.objects.filter(
            end_date__year=year,
            status__in=['approved', 'rejected', 'cancelled'],
            is_active=True
        ).update(
            is_active=False,
            archived_at=timezone.now()
        )

        # Archive old leave balances
        LeaveBalance.objects.filter(
            year=year,
            is_active=True
        ).update(
            is_active=False,
            archived_at=timezone.now()
        )

        # Archive past holidays
        Holiday.objects.filter(
            date__year=year,
            is_recurring=False,
            is_active=True
        ).update(
            is_active=False,
            archived_at=timezone.now()
        )

    def _generate_year_end_reports(self, year):
        """Generate comprehensive year-end reports"""
        from employees.models import Department

        # Generate overall attendance report
        call_command('generate_report', 
            year=year,
            format='excel',
            output=f'reports/year_end_{year}/attendance_summary_{year}.xlsx'
        )

        # Generate department-wise reports
        departments = Department.objects.filter(is_active=True)
        for dept in departments:
            call_command('generate_report',
                year=year,
                department=dept.id,
                format='excel',
                output=f'reports/year_end_{year}/attendance_{dept.code}_{year}.xlsx'
            )

        # Generate leave balance report
        call_command('generate_report',
            year=year,
            format='excel',
            type='leave_balance',
            output=f'reports/year_end_{year}/leave_balance_{year}.xlsx'
        )

        # Generate holiday report
        call_command('generate_report',
            year=year,
            format='excel',
            type='holiday',
            output=f'reports/year_end_{year}/holidays_{year}.xlsx'
        )
