from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from employees.models import Employee
from attendance.models import AttendanceRecord
import pandas as pd
import logging
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import attendance records from machine export file (Excel/CSV)'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the input file')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to see what would happen',
        )
        parser.add_argument(
            '--format',
            choices=['excel', 'csv'],
            default='excel',
            help='Input file format (default: excel)',
        )
        parser.add_argument(
            '--timezone',
            default='Asia/Riyadh',
            help='Timezone for timestamps (default: Asia/Riyadh)',
        )
        parser.add_argument(
            '--skip-rows',
            type=int,
            default=0,
            help='Number of header rows to skip',
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        dry_run = options['dry_run']
        file_format = options['format']
        tz = pytz.timezone(options['timezone'])
        skip_rows = options['skip_rows']

        self.stdout.write(
            self.style.SUCCESS(f'Starting attendance import from {file_path}')
        )
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - no changes will be made')
            )

        try:
            # Read the file
            if file_format == 'excel':
                df = pd.read_excel(file_path, skiprows=skip_rows)
            else:
                df = pd.read_csv(file_path, skiprows=skip_rows)

            # Expected columns with possible variations
            employee_id_cols = ['Personnel ID', 'Employee ID', 'ID', 'Badge']
            timestamp_cols = ['Date And Time', 'DateTime', 'Timestamp', 'Time']
            device_cols = ['Device Name', 'Device', 'Terminal']
            event_cols = ['Event Point', 'Event', 'Type']

            # Find actual column names in the file
            employee_id_col = next((col for col in employee_id_cols if col in df.columns), None)
            timestamp_col = next((col for col in timestamp_cols if col in df.columns), None)
            device_col = next((col for col in device_cols if col in df.columns), None)
            event_col = next((col for col in event_cols if col in df.columns), None)

            if not all([employee_id_col, timestamp_col]):
                raise CommandError('Required columns not found in the file')

            records_created = 0
            duplicates = 0
            errors = 0

            with transaction.atomic():
                for _, row in df.iterrows():
                    try:
                        # Get employee
                        employee_number = str(row[employee_id_col]).strip()
                        try:
                            employee = Employee.objects.get(employee_number=employee_number)
                        except Employee.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Employee not found: {employee_number}'
                                )
                            )
                            errors += 1
                            continue

                        # Parse timestamp
                        try:
                            timestamp = pd.to_datetime(row[timestamp_col])
                            timestamp = tz.localize(timestamp.replace(tzinfo=None))
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'Invalid timestamp for {employee_number}: {str(e)}'
                                )
                            )
                            errors += 1
                            continue

                        # Check for duplicate record
                        if AttendanceRecord.objects.filter(
                            employee=employee,
                            timestamp=timestamp,
                            is_active=True
                        ).exists():
                            duplicates += 1
                            continue

                        # Create attendance record
                        if not dry_run:
                            record = AttendanceRecord.objects.create(
                                employee=employee,
                                timestamp=timestamp,
                                device_name=row.get(device_col, ''),
                                event_point=row.get(event_col, ''),
                                source='import'
                            )
                            records_created += 1

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Error processing row: {str(e)}')
                        )
                        logger.error(f'Import error: {str(e)}', exc_info=True)
                        errors += 1
                        if not dry_run:
                            raise

                if dry_run:
                    transaction.set_rollback(True)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Dry run completed - would create {records_created} records\n'
                            f'Duplicates: {duplicates}\n'
                            f'Errors: {errors}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully created {records_created} records\n'
                            f'Duplicates: {duplicates}\n'
                            f'Errors: {errors}'
                        )
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing attendance records: {str(e)}')
            )
            logger.error(f'Attendance import failed: {str(e)}', exc_info=True)
            raise CommandError(str(e))
