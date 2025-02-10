import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import time

from attendance.models import Shift

logger = logging.getLogger(__name__)

DEFAULT_SHIFTS = [
    {
        'name': 'Regular Day Shift',
        'shift_type': 'REGULAR',
        'start_time': time(8, 0),  # 8:00 AM
        'end_time': time(17, 0),   # 5:00 PM
        'break_duration': 60,      # 1 hour lunch break
        'grace_period': 15,        # 15 minutes grace period
        'description': 'Standard working hours from 8 AM to 5 PM'
    },
    {
        'name': 'Night Shift',
        'shift_type': 'NIGHT',
        'start_time': time(20, 0),  # 8:00 PM
        'end_time': time(5, 0),     # 5:00 AM next day
        'break_duration': 45,       # 45 minutes break
        'grace_period': 15,
        'is_night_shift': True,
        'description': 'Night shift from 8 PM to 5 AM'
    },
    {
        'name': 'Morning Shift',
        'shift_type': 'REGULAR',
        'start_time': time(6, 0),   # 6:00 AM
        'end_time': time(14, 0),    # 2:00 PM
        'break_duration': 30,       # 30 minutes break
        'grace_period': 10,
        'description': 'Early morning shift from 6 AM to 2 PM'
    },
    {
        'name': 'Evening Shift',
        'shift_type': 'REGULAR',
        'start_time': time(14, 0),  # 2:00 PM
        'end_time': time(22, 0),    # 10:00 PM
        'break_duration': 45,       # 45 minutes break
        'grace_period': 15,
        'description': 'Evening shift from 2 PM to 10 PM'
    },
    {
        'name': 'Flexible Hours',
        'shift_type': 'FLEXIBLE',
        'start_time': time(7, 0),   # 7:00 AM
        'end_time': time(19, 0),    # 7:00 PM
        'break_duration': 60,
        'grace_period': 30,         # Longer grace period for flexible hours
        'description': 'Flexible working hours between 7 AM and 7 PM'
    },
    {
        'name': 'Split Shift',
        'shift_type': 'SPLIT',
        'start_time': time(9, 0),   # 9:00 AM
        'end_time': time(20, 0),    # 8:00 PM
        'break_duration': 180,      # 3 hours break
        'grace_period': 15,
        'description': 'Split shift with extended break in between'
    },
    {
        'name': 'Ramadan Shift',
        'shift_type': 'RAMADAN',
        'start_time': time(9, 0),   # 9:00 AM
        'end_time': time(15, 0),    # 3:00 PM
        'break_duration': 0,        # No break during Ramadan hours
        'grace_period': 15,
        'description': 'Reduced hours during Ramadan'
    }
]

class Command(BaseCommand):
    help = 'Initialize default shift types in the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of shift types even if they exist',
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                created_count = 0
                updated_count = 0
                skipped_count = 0

                for shift_data in DEFAULT_SHIFTS:
                    shift_name = shift_data['name']
                    
                    if options['force']:
                        # Update or create
                        shift, created = Shift.objects.update_or_create(
                            name=shift_name,
                            defaults={
                                **shift_data,
                                'created_at': timezone.now(),
                                'updated_at': timezone.now()
                            }
                        )
                        if created:
                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'Created shift: {shift_name}')
                            )
                        else:
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(f'Updated shift: {shift_name}')
                            )
                    else:
                        # Only create if doesn't exist
                        if not Shift.objects.filter(name=shift_name).exists():
                            Shift.objects.create(
                                **shift_data,
                                created_at=timezone.now(),
                                updated_at=timezone.now()
                            )
                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'Created shift: {shift_name}')
                            )
                        else:
                            skipped_count += 1
                            self.stdout.write(
                                self.style.WARNING(f'Skipped existing shift: {shift_name}')
                            )

                # Print summary
                self.stdout.write('\nSummary:')
                self.stdout.write(f'Created: {created_count}')
                if options['force']:
                    self.stdout.write(f'Updated: {updated_count}')
                else:
                    self.stdout.write(f'Skipped: {skipped_count}')
                self.stdout.write(
                    self.style.SUCCESS('Successfully initialized shift types')
                )

        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Error initializing shift types: {str(e)}')
            )
            logger.error('Error in init_shift_types command', exc_info=True)
