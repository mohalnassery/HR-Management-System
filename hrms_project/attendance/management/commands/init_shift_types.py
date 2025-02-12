import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import time

from attendance.models import Shift

logger = logging.getLogger(__name__)

DEFAULT_SHIFTS = [
    {
        'name': 'Default Shift',
        'shift_type': 'DEFAULT',
        'start_time': time(7, 0),        # Current timing
        'end_time': time(16, 0),         # Current timing
        'default_start_time': time(7, 0), # Default timing
        'default_end_time': time(16, 0),  # Default timing
        'break_duration': 60,
        'grace_period': 15
    },
    {
        'name': 'Open Shift',
        'shift_type': 'OPEN',
        'start_time': time(8, 0),        # Current timing
        'end_time': time(17, 0),         # Current timing
        'default_start_time': time(8, 0), # Default timing
        'default_end_time': time(17, 0),  # Default timing
        'break_duration': 60,
        'grace_period': 15
    },
    {
        'name': 'Night Shift Default',
        'shift_type': 'NIGHT',
        'start_time': time(19, 0),        # Current timing
        'end_time': time(4, 0),          # Current timing
        'default_start_time': time(19, 0), # Default timing
        'default_end_time': time(4, 0),    # Default timing
        'break_duration': 60,
        'grace_period': 15
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
