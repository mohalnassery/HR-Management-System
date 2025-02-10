import logging
from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from attendance.models import RamadanPeriod

logger = logging.getLogger(__name__)

# Sample Ramadan periods for the next few years
# Dates are approximate and should be adjusted based on actual calendar
SAMPLE_PERIODS = [
    {
        'year': 2024,
        'start_date': date(2024, 3, 11),
        'end_date': date(2024, 4, 9),
        'is_active': True,
    },
    {
        'year': 2025,
        'start_date': date(2025, 3, 1),
        'end_date': date(2025, 3, 30),
        'is_active': False,
    },
    {
        'year': 2026,
        'start_date': date(2026, 2, 18),
        'end_date': date(2026, 3, 19),
        'is_active': False,
    }
]

class Command(BaseCommand):
    help = 'Initialize sample Ramadan periods in the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of Ramadan periods even if they exist',
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                created_count = 0
                updated_count = 0
                skipped_count = 0

                for period_data in SAMPLE_PERIODS:
                    year = period_data['year']

                    if options['force']:
                        # Update or create
                        period, created = RamadanPeriod.objects.update_or_create(
                            year=year,
                            defaults={
                                **period_data,
                                'created_at': timezone.now(),
                                'updated_at': timezone.now()
                            }
                        )
                        if created:
                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'Created Ramadan period for {year}')
                            )
                        else:
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(f'Updated Ramadan period for {year}')
                            )
                    else:
                        # Only create if doesn't exist
                        if not RamadanPeriod.objects.filter(year=year).exists():
                            RamadanPeriod.objects.create(
                                **period_data,
                                created_at=timezone.now(),
                                updated_at=timezone.now()
                            )
                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'Created Ramadan period for {year}')
                            )
                        else:
                            skipped_count += 1
                            self.stdout.write(
                                self.style.WARNING(f'Skipped existing period for {year}')
                            )

                # Print summary
                self.stdout.write('\nSummary:')
                self.stdout.write(f'Created: {created_count}')
                if options['force']:
                    self.stdout.write(f'Updated: {updated_count}')
                else:
                    self.stdout.write(f'Skipped: {skipped_count}')
                self.stdout.write(
                    self.style.SUCCESS('Successfully initialized Ramadan periods')
                )

        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Error initializing Ramadan periods: {str(e)}')
            )
            logger.error('Error in init_ramadan_periods command', exc_info=True)

    def validate_period(self, start_date, end_date):
        """Validate Ramadan period dates"""
        if end_date < start_date:
            raise ValueError("End date cannot be before start date")

        duration = (end_date - start_date).days + 1
        if duration < 28 or duration > 31:
            raise ValueError(f"Invalid duration: {duration} days")

        if start_date.year != end_date.year:
            raise ValueError("Start and end dates must be in the same year")

        return True
