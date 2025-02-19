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
                        'code': 'ANNUAL',
                        'name': 'Annual Leave',
                        'description': 'Standard annual leave with full day and half day options',
                        'category': 'REGULAR',
                        'days_allowed': 30,  # Standard annual leave allowance
                        'is_paid': True,
                        'requires_document': False,
                        'gender_specific': 'A',
                        'accrual_enabled': True,
                        'accrual_days': 2.5,
                        'accrual_period': 'MONTHLY',
                        'reset_period': 'YEARLY',
                    },
                    {
                        'code': 'EMERG',
                        'name': 'Emergency Leave',
                        'description': 'For emergency situations requiring immediate leave (employer discretion)',
                        'category': 'SPECIAL',
                        'days_allowed': 5,
                        'is_paid': True,
                        'requires_document': False,
                        'gender_specific': 'A',
                        'accrual_enabled': False,
                        'reset_period': 'YEARLY',
                    },
                    {
                        'code': 'HALF_DAY',
                        'name': 'Half Day Leave',
                        'description': 'Half day leave options for morning or afternoon',
                        'category': 'REGULAR',
                        'days_allowed': 0,  # Deducted from annual leave balance
                        'is_paid': True,
                        'requires_document': False,
                        'gender_specific': 'A',
                        'accrual_enabled': False,
                        'reset_period': 'YEARLY',
                    },
                    {
                        'code': 'INJURY',
                        'name': 'Injury Leave',
                        'description': 'Leave for work-related injuries as per Social Insurance Law, Legislative Decree No.(24) of 1976',
                        'category': 'MEDICAL',
                        'days_allowed': 180,  # 6 months as per law
                        'is_paid': True,
                        'requires_document': True,
                        'gender_specific': 'A',
                        'accrual_enabled': False,
                        'reset_period': 'NEVER',
                    },
                    {
                        'code': 'MARRIAGE',
                        'name': 'Marriage Leave',
                        'description': 'Leave for employee marriage (Article 4)',
                        'category': 'SPECIAL',
                        'days_allowed': 3,
                        'is_paid': True,
                        'requires_document': True,
                        'gender_specific': 'A',
                        'accrual_enabled': False,
                        'reset_period': 'NEVER',  # One-time leave
                    },
                    {
                        'code': 'MATERNITY',
                        'name': 'Maternity Leave',
                        'description': 'Maternity leave for female employees (Article 34). 60 days paid + 15 days unpaid',
                        'category': 'SPECIAL',
                        'days_allowed': 75,  # Total days (60 paid + 15 unpaid)
                        'is_paid': True,  # System will handle partial paid days
                        'requires_document': True,
                        'gender_specific': 'F',
                        'accrual_enabled': False,
                        'reset_period': 'EVENT',  # Per pregnancy
                    },
                    {
                        'code': 'PATERNITY',
                        'name': 'Paternity Leave',
                        'description': 'Paternity leave for male employees (Article 4)',
                        'category': 'SPECIAL',
                        'days_allowed': 1,
                        'is_paid': True,
                        'requires_document': True,
                        'gender_specific': 'M',
                        'accrual_enabled': False,
                        'reset_period': 'EVENT',  # Per child
                    },
                    {
                        'code': 'PERMISSION',
                        'name': 'Permission Leave',
                        'description': 'Short duration leave with employer discretion',
                        'category': 'REGULAR',
                        'days_allowed': 3,
                        'is_paid': True,
                        'requires_document': False,
                        'gender_specific': 'A',
                        'accrual_enabled': False,
                        'reset_period': 'YEARLY',
                    },
                    {
                        'code': 'DEATH',
                        'name': 'Relative Death Leave',
                        'description': 'Compassionate leave for death of relatives (Article 4). 30 days for widow, 3 days for others',
                        'category': 'SPECIAL',
                        'days_allowed': 30,  # Max days (for widow)
                        'is_paid': True,
                        'requires_document': True,
                        'gender_specific': 'A',
                        'accrual_enabled': False,
                        'reset_period': 'EVENT',
                    },
                    {
                        'code': 'SICK',
                        'name': 'Sick Leave',
                        'description': 'Sick leave with three tiers (Article 56). 15 days full pay, 20 days half pay, 20 days unpaid',
                        'category': 'MEDICAL',
                        'days_allowed': 55,  # Total of all tiers
                        'is_paid': True,  # System will handle partial paid days
                        'requires_document': True,
                        'gender_specific': 'A',
                        'accrual_enabled': False,
                        'reset_period': 'YEARLY',
                    },
                    {
                        'code': 'HAJJ',
                        'name': 'Hajj Leave',
                        'description': 'Leave for performing Hajj pilgrimage (Article 61)',
                        'category': 'SPECIAL',
                        'days_allowed': 14,
                        'is_paid': True,
                        'requires_document': True,
                        'gender_specific': 'A',
                        'accrual_enabled': False,
                        'reset_period': 'NEVER',  # Once during employment
                    },
                    {
                        'code': 'IDDAH',
                        'name': 'Iddah Leave',
                        'description': 'Iddah leave for Muslim female employees (Article 35). 30 days paid + 100 days unpaid',
                        'category': 'SPECIAL',
                        'days_allowed': 130,  # Total days (30 paid + 100 unpaid)
                        'is_paid': True,  # System will handle partial paid days
                        'requires_document': True,
                        'gender_specific': 'F',
                        'accrual_enabled': False,
                        'reset_period': 'EVENT',
                    }
                ]

                # Create leave types
                for leave_type in leave_types:
                    LeaveType.objects.create(**leave_type)

                self.stdout.write(
                    self.style.SUCCESS('Successfully initialized leave types')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to initialize leave types: {str(e)}')
            )
            raise e
