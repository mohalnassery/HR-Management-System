from django.core.management.base import BaseCommand
from django.db import transaction
from attendance.models import LeaveType
import logging
import json

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
        if LeaveType.objects.exists():
            if force:
                # Delete existing leave types when using --force
                self.stdout.write(
                    self.style.WARNING('Deleting existing leave types...')
                )
                LeaveType.objects.all().delete()
            else:
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
                        'days_allowed': 30,
                        'is_paid': True,
                        'requires_document': False,
                        'gender_specific': 'A',
                        'accrual_enabled': True,
                        'accrual_days': 2.5,
                        'accrual_period': 'MONTHLY',
                        'reset_period': 'YEARLY',
                        'balance_calculation': 'ACCRUAL',
                        'validation_rules': json.dumps({
                            'is_one_time': False,
                            'has_fixed_duration': False,
                            'min_days': 0.5,
                            'max_days': 30
                        })
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
                        'balance_calculation': 'FIXED',
                        'validation_rules': json.dumps({
                            'is_one_time': False,
                            'has_fixed_duration': False,
                            'min_days': 0.5,
                            'max_days': 5
                        })
                    },
                    {
                        'code': 'HALF',
                        'name': 'Half Day Leave',
                        'description': 'Half day leave options for morning or afternoon',
                        'category': 'REGULAR',
                        'days_allowed': 0,
                        'is_paid': True,
                        'requires_document': False,
                        'gender_specific': 'A',
                        'accrual_enabled': False,
                        'reset_period': 'YEARLY',
                        'balance_calculation': 'SHARED',
                        'shared_balance_with': 'ANNUAL',
                        'validation_rules': json.dumps({
                            'is_one_time': False,
                            'has_fixed_duration': True,
                            'fixed_duration': 0.5
                        })
                    },
                    {
                        'code': 'INJURY',
                        'name': 'Injury Leave',
                        'description': 'Leave for work-related injuries as per Social Insurance Law, Legislative Decree No.(24) of 1976',
                        'category': 'MEDICAL',
                        'days_allowed': 180,
                        'is_paid': True,
                        'requires_document': True,
                        'gender_specific': 'A',
                        'accrual_enabled': False,
                        'reset_period': 'NEVER',
                        'balance_calculation': 'FIXED',
                        'validation_rules': json.dumps({
                            'is_one_time': False,
                            'has_fixed_duration': False,
                            'min_days': 1,
                            'max_days': 180
                        })
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
                        'reset_period': 'NEVER',
                        'balance_calculation': 'FIXED',
                        'validation_rules': json.dumps({
                            'is_one_time': True,
                            'has_fixed_duration': True,
                            'fixed_duration': 3
                        })
                    },
                    {
                        'code': 'MATERNITY',
                        'name': 'Maternity Leave',
                        'description': 'Maternity leave for female employees (Article 34). 60 days paid + 15 days unpaid',
                        'category': 'SPECIAL',
                        'days_allowed': 75,
                        'is_paid': True,
                        'requires_document': True,
                        'gender_specific': 'F',
                        'accrual_enabled': False,
                        'reset_period': 'EVENT',
                        'balance_calculation': 'FIXED',
                        'validation_rules': json.dumps({
                            'is_one_time': False,
                            'has_fixed_duration': True,
                            'fixed_duration': 75,
                            'sub_types': [
                                {'code': 'paid_60', 'days': 60, 'paid': True},
                                {'code': 'unpaid_15', 'days': 15, 'paid': False}
                            ]
                        })
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
                        'reset_period': 'EVENT',
                        'balance_calculation': 'FIXED',
                        'validation_rules': json.dumps({
                            'is_one_time': False,
                            'has_fixed_duration': True,
                            'fixed_duration': 1
                        })
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
                        'balance_calculation': 'FIXED',
                        'validation_rules': json.dumps({
                            'is_one_time': False,
                            'has_fixed_duration': False,
                            'min_days': 0.5,
                            'max_days': 3
                        })
                    },
                    {
                        'code': 'DEATH',
                        'name': 'Relative Death Leave',
                        'description': 'Compassionate leave for death of relatives (Article 4). 30 days for widow, 3 days for others',
                        'category': 'SPECIAL',
                        'days_allowed': 30,
                        'is_paid': True,
                        'requires_document': True,
                        'gender_specific': 'A',
                        'accrual_enabled': False,
                        'reset_period': 'EVENT',
                        'balance_calculation': 'FIXED',
                        'validation_rules': json.dumps({
                            'is_one_time': False,
                            'has_fixed_duration': True,
                            'sub_types': [
                                {'code': 'spouse_30', 'days': 30, 'description': "Woman's Husband"},
                                {'code': 'spouse_3', 'days': 3, 'description': "Man's Wife"},
                                {'code': 'first_degree', 'days': 3, 'description': 'First Degree Relative'},
                                {'code': 'second_degree', 'days': 3, 'description': 'Second Degree Spouse Relative'}
                            ]
                        })
                    },
                    {
                        'code': 'SICK',
                        'name': 'Sick Leave',
                        'description': 'Sick leave with three tiers (Article 56). 15 days full pay, 20 days half pay, 20 days unpaid',
                        'category': 'MEDICAL',
                        'days_allowed': 55,
                        'is_paid': True,
                        'requires_document': True,
                        'gender_specific': 'A',
                        'accrual_enabled': False,
                        'reset_period': 'YEARLY',
                        'balance_calculation': 'TIERED',
                        'validation_rules': json.dumps({
                            'is_one_time': False,
                            'has_fixed_duration': False,
                            'tiers': [
                                {'name': 'Full Pay', 'days': 15, 'pay_percentage': 100},
                                {'name': 'Half Pay', 'days': 20, 'pay_percentage': 50},
                                {'name': 'No Pay', 'days': 20, 'pay_percentage': 0}
                            ]
                        })
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
                        'reset_period': 'NEVER',
                        'balance_calculation': 'FIXED',
                        'validation_rules': json.dumps({
                            'is_one_time': True,
                            'has_fixed_duration': True,
                            'fixed_duration': 14
                        })
                    },
                    {
                        'code': 'IDDAH',
                        'name': 'Iddah Leave',
                        'description': 'Iddah leave for Muslim female employees (Article 35). 30 days paid + 100 days unpaid',
                        'category': 'SPECIAL',
                        'days_allowed': 130,
                        'is_paid': True,
                        'requires_document': True,
                        'gender_specific': 'F',
                        'accrual_enabled': False,
                        'reset_period': 'EVENT',
                        'balance_calculation': 'FIXED',
                        'validation_rules': json.dumps({
                            'is_one_time': False,
                            'has_fixed_duration': True,
                            'sub_types': [
                                {'code': 'paid_30', 'days': 30, 'paid': True},
                                {'code': 'unpaid_100', 'days': 100, 'paid': False}
                            ]
                        })
                    }
                ]

                # Create leave types
                for leave_type_data in leave_types:
                    # Handle shared balance reference
                    shared_balance_with = leave_type_data.pop('shared_balance_with', None)
                    leave_type = LeaveType.objects.create(**leave_type_data)
                    
                    # Update shared balance reference after all types are created
                    if shared_balance_with:
                        try:
                            referenced_type = LeaveType.objects.get(code=shared_balance_with)
                            leave_type.shared_balance_with = referenced_type
                            leave_type.save()
                        except LeaveType.DoesNotExist:
                            logger.warning(f"Referenced leave type {shared_balance_with} not found for {leave_type.code}")

                self.stdout.write(
                    self.style.SUCCESS('Successfully initialized leave types')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to initialize leave types: {str(e)}')
            )
            raise e
