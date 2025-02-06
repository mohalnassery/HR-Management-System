from django.db import migrations

def create_leave_types(apps, schema_editor):
    LeaveType = apps.get_model('attendance', 'LeaveType')

    leave_types = [
        # Emergency Leave
        {
            'name': 'Emergency Leave',
            'code': 'EMERG',
            'category': 'REGULAR',
            'description': 'Emergency leave up to 15 days per year',
            'days_allowed': 15,
            'is_paid': True,
            'requires_document': False,
            'gender_specific': 'A',
            'accrual_enabled': False,
            'reset_period': 'YEARLY'
        },
        # Annual Leave
        {
            'name': 'Annual Leave',
            'code': 'ANNUAL',
            'category': 'REGULAR',
            'description': 'Annual leave accrued at 2.5 days per 30 working days',
            'days_allowed': 30,
            'is_paid': True,
            'requires_document': False,
            'gender_specific': 'A',
            'accrual_enabled': True,
            'accrual_days': 2.5,
            'accrual_period': 'WORKED',
            'reset_period': 'YEARLY'
        },
        # Half Day Leave
        {
            'name': 'Half Day Leave',
            'code': 'HALF',
            'category': 'REGULAR',
            'description': 'Half day leave deducted from annual leave balance',
            'days_allowed': 0,  # Deducted from annual leave
            'is_paid': True,
            'requires_document': False,
            'gender_specific': 'A',
            'accrual_enabled': False,
            'reset_period': 'NEVER'
        },
        # Permission Leave
        {
            'name': 'Permission Leave',
            'code': 'PERM',
            'category': 'REGULAR',
            'description': 'Short permission tracked in hours (8 hours = 1 day)',
            'days_allowed': 3,
            'is_paid': True,
            'requires_document': False,
            'gender_specific': 'A',
            'accrual_enabled': False,
            'reset_period': 'YEARLY'
        },
        # Regular Sick Leave - Tier 1
        {
            'name': 'Sick Leave - Tier 1',
            'code': 'SICK1',
            'category': 'MEDICAL',
            'description': 'First 15 days of sick leave (fully paid)',
            'days_allowed': 15,
            'is_paid': True,
            'requires_document': True,
            'gender_specific': 'A',
            'accrual_enabled': False,
            'reset_period': 'YEARLY'
        },
        # Regular Sick Leave - Tier 2
        {
            'name': 'Sick Leave - Tier 2',
            'code': 'SICK2',
            'category': 'MEDICAL',
            'description': 'Next 20 days of sick leave (half paid)',
            'days_allowed': 20,
            'is_paid': True,
            'requires_document': True,
            'gender_specific': 'A',
            'accrual_enabled': False,
            'reset_period': 'YEARLY'
        },
        # Regular Sick Leave - Tier 3
        {
            'name': 'Sick Leave - Tier 3',
            'code': 'SICK3',
            'category': 'MEDICAL',
            'description': 'Final 20 days of sick leave (unpaid)',
            'days_allowed': 20,
            'is_paid': False,
            'requires_document': True,
            'gender_specific': 'A',
            'accrual_enabled': False,
            'reset_period': 'YEARLY'
        },
        # Injury Leave
        {
            'name': 'Injury Leave',
            'code': 'INJURY',
            'category': 'MEDICAL',
            'description': 'Unlimited paid leave for work-related injuries',
            'days_allowed': 0,  # Unlimited
            'is_paid': True,
            'requires_document': True,
            'gender_specific': 'A',
            'accrual_enabled': False,
            'reset_period': 'EVENT'
        },
        # Relative Death Leave
        {
            'name': 'Relative Death Leave',
            'code': 'DEATH',
            'category': 'SPECIAL',
            'description': '3 days paid leave per death event',
            'days_allowed': 3,
            'is_paid': True,
            'requires_document': True,
            'gender_specific': 'A',
            'accrual_enabled': False,
            'reset_period': 'EVENT'
        },
        # Maternity Leave
        {
            'name': 'Maternity Leave',
            'code': 'MATER',
            'category': 'SPECIAL',
            'description': '60 days paid leave for childbirth',
            'days_allowed': 60,
            'is_paid': True,
            'requires_document': True,
            'gender_specific': 'F',
            'accrual_enabled': False,
            'reset_period': 'EVENT'
        },
        # Paternity Leave
        {
            'name': 'Paternity Leave',
            'code': 'PATER',
            'category': 'SPECIAL',
            'description': '1 day paid leave for childbirth',
            'days_allowed': 1,
            'is_paid': True,
            'requires_document': True,
            'gender_specific': 'M',
            'accrual_enabled': False,
            'reset_period': 'EVENT'
        },
        # Marriage Leave
        {
            'name': 'Marriage Leave',
            'code': 'MARR',
            'category': 'SPECIAL',
            'description': '3 days paid leave per marriage event',
            'days_allowed': 3,
            'is_paid': True,
            'requires_document': True,
            'gender_specific': 'A',
            'accrual_enabled': False,
            'reset_period': 'EVENT'
        },
    ]

    for leave_type in leave_types:
        LeaveType.objects.create(**leave_type)

def remove_leave_types(apps, schema_editor):
    LeaveType = apps.get_model('attendance', 'LeaveType')
    LeaveType.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('attendance', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_leave_types, remove_leave_types),
    ]
