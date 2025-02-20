import logging
from datetime import date
from typing import Dict, Any, Tuple, List
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from attendance.models import RamadanPeriod
from attendance.services.ramadan_service import RamadanService

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

class RamadanPeriodInitializer:
    """Handles Ramadan period initialization logic"""
    
    def __init__(self, command_instance: BaseCommand):
        self.command = command_instance
        self.ramadan_service = RamadanService()
        self.created_count = 0
        self.updated_count = 0
        self.skipped_count = 0

    def process_period(self, period_data: Dict[str, Any], force: bool = False) -> None:
        """
        Process a single Ramadan period - create, update, or skip based on force flag.
        
        Args:
            period_data: Dictionary containing period data
            force: Whether to force update existing periods
        """
        year = period_data['year']
        
        try:
            # Validate period dates using RamadanService
            self.ramadan_service.validate_period_dates(
                period_data['start_date'],
                period_data['end_date']
            )
            
            # Add timestamps
            period_data = {
                **period_data,
                'created_at': timezone.now(),
                'updated_at': timezone.now()
            }
            
            if force:
                self._update_or_create_period(year, period_data)
            else:
                self._create_if_not_exists(year, period_data)
                
        except Exception as e:
            self.command.stderr.write(
                self.command.style.ERROR(f'Error processing period for {year}: {str(e)}')
            )
            logger.error(f'Error processing Ramadan period for {year}', exc_info=True)

    def _update_or_create_period(self, year: int, period_data: Dict[str, Any]) -> None:
        """Update existing period or create new one"""
        period, created = RamadanPeriod.objects.update_or_create(
            year=year,
            defaults=period_data
        )
        
        if created:
            self.created_count += 1
            self.command.stdout.write(
                self.command.style.SUCCESS(f'Created Ramadan period for {year}')
            )
        else:
            self.updated_count += 1
            self.command.stdout.write(
                self.command.style.WARNING(f'Updated Ramadan period for {year}')
            )

    def _create_if_not_exists(self, year: int, period_data: Dict[str, Any]) -> None:
        """Create period only if it doesn't exist"""
        if not RamadanPeriod.objects.filter(year=year).exists():
            RamadanPeriod.objects.create(**period_data)
            self.created_count += 1
            self.command.stdout.write(
                self.command.style.SUCCESS(f'Created Ramadan period for {year}')
            )
        else:
            self.skipped_count += 1
            self.command.stdout.write(
                self.command.style.WARNING(f'Skipped existing period for {year}')
            )

    def print_summary(self, force: bool) -> None:
        """Print summary of operations performed"""
        self.command.stdout.write('\nSummary:')
        self.command.stdout.write(f'Created: {self.created_count}')
        if force:
            self.command.stdout.write(f'Updated: {self.updated_count}')
        else:
            self.command.stdout.write(f'Skipped: {self.skipped_count}')
        self.command.stdout.write(
            self.command.style.SUCCESS('Successfully initialized Ramadan periods')
        )

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
            initializer = RamadanPeriodInitializer(self)
            
            with transaction.atomic():
                # Process each period
                for period_data in SAMPLE_PERIODS:
                    initializer.process_period(period_data, options['force'])
                
                # Print summary
                initializer.print_summary(options['force'])

        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Error initializing Ramadan periods: {str(e)}')
            )
            logger.error('Error in init_ramadan_periods command', exc_info=True)
