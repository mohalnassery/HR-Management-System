from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime
from attendance.models import AttendanceLog
from attendance.services.attendance_status_service import AttendanceStatusService

class Command(BaseCommand):
    help = 'Recalculate attendance status for existing AttendanceLogs'

    def add_arguments(self, parser):
        parser.add_argument('--date', type=str, help='Process logs for a specific date (YYYY-MM-DD)')
        parser.add_argument('--date-range', nargs=2, type=str, help='Process logs for a date range (YYYY-MM-DD YYYY-MM-DD)')
        parser.add_argument('--employee-id', type=int, help='Process logs for a specific employee ID')

    def handle(self, *args, **options):
        queryset = AttendanceLog.objects.all()
        processed = 0
        errors = 0

        try:
            # Filter by date if specified
            if options['date']:
                try:
                    process_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
                    queryset = queryset.filter(date=process_date)
                    self.stdout.write(f'Filtering logs for date: {process_date}')
                except ValueError:
                    raise CommandError('Invalid date format. Use YYYY-MM-DD')

            # Filter by date range if specified
            elif options['date_range']:
                try:
                    start_date = datetime.strptime(options['date_range'][0], '%Y-%m-%d').date()
                    end_date = datetime.strptime(options['date_range'][1], '%Y-%m-%d').date()
                    if start_date > end_date:
                        raise CommandError('Start date must be before end date')
                    queryset = queryset.filter(date__range=[start_date, end_date])
                    self.stdout.write(f'Filtering logs between {start_date} and {end_date}')
                except ValueError:
                    raise CommandError('Invalid date format in range. Use YYYY-MM-DD')

            # Filter by employee if specified
            if options['employee_id']:
                queryset = queryset.filter(employee_id=options['employee_id'])
                self.stdout.write(f'Filtering logs for employee ID: {options["employee_id"]}')

            total_logs = queryset.count()
            if total_logs == 0:
                self.stdout.write(self.style.WARNING('No attendance logs found matching the criteria'))
                return

            self.stdout.write(f'Found {total_logs} attendance logs to process')
            self.stdout.write('Starting reprocessing...')

            # Process each log
            for log in queryset:
                try:
                    self.stdout.write(f'Processing log ID {log.id} for {log.date}...', ending='\r')
                    AttendanceStatusService.update_attendance_status(log)
                    processed += 1
                except Exception as e:
                    self.stderr.write(f'\nError processing log ID {log.id}: {str(e)}')
                    errors += 1

            # Summary
            self.stdout.write('\n' + self.style.SUCCESS(f'Successfully processed {processed} attendance logs'))
            if errors > 0:
                self.stdout.write(self.style.WARNING(f'Encountered {errors} errors during processing'))

        except Exception as e:
            raise CommandError(f'An error occurred: {str(e)}')
