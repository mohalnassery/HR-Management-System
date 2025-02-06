from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from attendance.models import Holiday
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate holidays for next year based on recurring holidays'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to see what would happen',
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Specify year to generate (defaults to next year)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force generation even if not December',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        target_year = options['year'] or timezone.now().year + 1
        current_month = timezone.now().month

        # Check if it's December or force flag is set
        if current_month != 12 and not force:
            self.stdout.write(
                self.style.WARNING(
                    'Holiday generation should be run in December. '
                    'Use --force to override.'
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Starting holiday generation for year {target_year}')
        )
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - no changes will be made')
            )

        try:
            with transaction.atomic():
                # Get all recurring holidays
                recurring_holidays = Holiday.objects.filter(
                    is_recurring=True,
                    is_active=True
                )

                self.stdout.write(
                    f'Found {recurring_holidays.count()} recurring holidays'
                )

                holidays_created = 0
                holidays_skipped = 0

                # Process each recurring holiday
                for holiday in recurring_holidays:
                    # Create date for target year
                    try:
                        new_date = holiday.date.replace(year=target_year)
                        
                        # Check if holiday already exists
                        existing = Holiday.objects.filter(
                            date=new_date,
                            name=holiday.name
                        ).exists()
                        
                        if existing:
                            self.stdout.write(
                                f'  Skipping {holiday.name} - already exists on {new_date}'
                            )
                            holidays_skipped += 1
                            continue

                        # Create new holiday instance
                        if not dry_run:
                            new_holiday = Holiday.objects.create(
                                date=new_date,
                                name=holiday.name,
                                description=holiday.description,
                                holiday_type=holiday.holiday_type,
                                is_paid=holiday.is_paid,
                                is_recurring=False  # New instance is not recurring
                            )
                            
                            # Copy department associations if any
                            if holiday.applicable_departments.exists():
                                new_holiday.applicable_departments.set(
                                    holiday.applicable_departments.all()
                                )

                        self.stdout.write(
                            f'  Created {holiday.name} on {new_date}'
                        )
                        holidays_created += 1

                    except Exception as e:
                        logger.error(
                            f'Error processing holiday {holiday.name}: {str(e)}'
                        )
                        if not dry_run:
                            raise

                if dry_run:
                    transaction.set_rollback(True)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Dry run completed - would create {holidays_created} '
                            f'holidays ({holidays_skipped} skipped)'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully created {holidays_created} holidays '
                            f'({holidays_skipped} skipped)'
                        )
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating holidays: {str(e)}')
            )
            logger.error(f'Holiday generation failed: {str(e)}')
            raise
