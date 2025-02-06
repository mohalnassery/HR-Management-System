from django.core.management.base import BaseCommand
from django.db import transaction
from attendance.models import LeaveType
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Initialize default leave types with standard configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if leave types exist',
        )

    def handle(self, *args, **options):
        force = options['force']

        # Check if leave types already exist
        if LeaveType.objects.exists() and not force:
            self.stdout.write(
                self.style.WARNING(
                    'Leave types already exist. Use --force to reinitialize.'
                )
            )
            return

        try:
            with transaction.atomic():
                # Define default leave types
                leave_types = [
                    {
                        'code': 'EMERG',
                        'name': 'Emergency Leave',
                        'description': 'For emergency situations requiring immediate leave',
                        'default_days': 15,
                        'accrual_type': 'fixed',
                        'requires_document': False,
                        'reset_period': 'yearly',
                        'allow_carryover': False,
                        'gender_specific': 'A',  # All genders
                        'is_paid': True,
                    },
                    {
                        'code': 'ANNUAL',
                        'name': 'Annual Leave',
                        'description': 'Standard annual leave accrued based on working days',
                        'default_days': 0,  # Accrued at 2.5 days per 30 worked days
                        'accrual_type': 'periodic',
                        'accrual_rate': 2.5,
                        'accrual_period': 30,
                        'requires_document': False,
                        'reset_period': 'yearly',
                        'allow_carryover': True,
                        'max_carryover': 30,
                        'gender_specific': 'A',
                    },
                    {
                        'code': 'SICK_REG',
                        'name': 'Sick Leave (Regular)',
                        'description': 'Regular sick leave with three tiers',
                        'default_days': 15,  # Tier 1
                        'accrual_type': 'fixed',
                        'requires_document': True,
                        'reset_period': 'yearly',
                        'allow_carryover': False,
                        'gender_specific': 'A',
                        'is_paid': True,
                        'has_tiers': True,
                        'tier_2_days': 20,  # Half paid
                        'tier_3_days': 20,  # Unpaid
                    },
                    {
                        'code': 'INJURY',
                        'name': 'Injury Leave',
                        'description': 'Leave for work-related injuries',
                        'default_days': 365,  # Unlimited but set to 1 year for tracking
                        'accrual_type': 'fixed',
                        'requires_document': True,
                        'reset_period': 'never',
                        'allow_carryover': True,
                        'gender_specific': 'A',
                        'is_paid': True,
                    },
                    {
                        'code': 'MATERNITY',
                        'name': 'Maternity Leave',
                        'description': 'Maternity leave for female employees',
                        'default_days': 60,
                        'accrual_type': 'fixed',
                        'requires_document': True,
                        'reset_period': 'never',
                        'allow_carryover': False,
                        'gender_specific': 'F',
                        'is_paid': True,
                    },
                    {
                        'code': 'PATERNITY',
                        'name': 'Paternity Leave',
                        'description': 'Paternity leave for male employees',
                        'default_days': 1,
                        'accrual_type': 'fixed',
                        'requires_document': True,
                        'reset_period': 'never',
                        'allow_carryover': False,
                        'gender_specific': 'M',
                        'is_paid': True,
                    },
                    {
                        'code': 'MARRIAGE',
                        'name': 'Marriage Leave',
                        'description': 'Leave for employee marriage',
                        'default_days': 3,
                        'accrual_type': 'fixed',
                        'requires_document': True,
                        'reset_period': 'never',
                        'allow_carryover': False,
                        'gender_specific': 'A',
                        'is_paid': True,
                    },
                    {
                        'code': 'DEATH',
                        'name': 'Relative Death Leave',
                        'description': 'Leave for death of immediate family member',
                        'default_days': 3,
                        'accrual_type': 'fixed',
                        'requires_document': True,
                        'reset_period': 'never',
                        'allow_carryover': False,
                        'gender_specific': 'A',
                        'is_paid': True,
                    },
                    {
                        'code': 'PERM',
                        'name': 'Permission Leave',
                        'description': 'Short permission leave (tracked in hours)',
                        'default_days': 8,  # 8 hours = 1 day
                        'accrual_type': 'fixed',
                        'requires_document': False,
                        'reset_period': 'monthly',
                        'allow_carryover': False,
                        'gender_specific': 'A',
                        'is_paid': True,
                        'unit_type': 'hours',
                    },
                ]

                for leave_type_data in leave_types:
                    leave_type = LeaveType.objects.create(**leave_type_data)
                    self.stdout.write(
                        f'Created leave type: {leave_type.name}'
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully initialized {len(leave_types)} leave types'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error initializing leave types: {str(e)}')
            )
            logger.error(f'Leave type initialization failed: {str(e)}')
            raise
