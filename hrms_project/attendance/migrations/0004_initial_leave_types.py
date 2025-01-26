from django.db import migrations

def create_leave_types(apps, schema_editor):
    LeaveType = apps.get_model('attendance', 'LeaveType')
    
    # Emergency Leave
    LeaveType.objects.create(
        name='Emergency Leave',
        code='EMERGENCY',
        category='REGULAR',
        description='Emergency leave with 15 days per year allowance',
        days_allowed=15,
        is_paid=True,
        requires_document=False,
        gender_specific='A',
        reset_period='YEARLY'
    )
    
    # Annual Leave
    LeaveType.objects.create(
        name='Annual Leave',
        code='ANNUAL',
        category='REGULAR',
        description='Annual leave accrued at 2.5 days per 30 working days',
        days_allowed=30,
        is_paid=True,
        requires_document=False,
        gender_specific='A',
        accrual_enabled=True,
        accrual_days=2.5,
        accrual_period='WORKED',
        reset_period='YEARLY'
    )
    
    # Half Day Leave
    LeaveType.objects.create(
        name='Half Day Leave',
        code='HALF_DAY',
        category='REGULAR',
        description='Half day leave deducted from annual leave balance',
        days_allowed=0,  # Uses annual leave balance
        is_paid=True,
        requires_document=False,
        gender_specific='A',
        reset_period='NEVER'
    )
    
    # Permission Leave
    LeaveType.objects.create(
        name='Permission Leave',
        code='PERMISSION',
        category='REGULAR',
        description='Hourly permission leave (8 hours = 1 day)',
        days_allowed=8,  # In hours
        is_paid=True,
        requires_document=False,
        gender_specific='A',
        reset_period='YEARLY'
    )
    
    # Sick Leave - Tier 1
    LeaveType.objects.create(
        name='Sick Leave - Tier 1',
        code='SICK_T1',
        category='MEDICAL',
        description='First 15 days of sick leave (Fully paid)',
        days_allowed=15,
        is_paid=True,
        requires_document=True,
        gender_specific='A',
        reset_period='YEARLY'
    )
    
    # Sick Leave - Tier 2
    LeaveType.objects.create(
        name='Sick Leave - Tier 2',
        code='SICK_T2',
        category='MEDICAL',
        description='Next 20 days of sick leave (Half paid)',
        days_allowed=20,
        is_paid=True,
        requires_document=True,
        gender_specific='A',
        reset_period='YEARLY'
    )
    
    # Sick Leave - Tier 3
    LeaveType.objects.create(
        name='Sick Leave - Tier 3',
        code='SICK_T3',
        category='MEDICAL',
        description='Final 20 days of sick leave (Unpaid)',
        days_allowed=20,
        is_paid=False,
        requires_document=True,
        gender_specific='A',
        reset_period='YEARLY'
    )
    
    # Injury Leave
    LeaveType.objects.create(
        name='Injury Leave',
        code='INJURY',
        category='MEDICAL',
        description='Injury leave with unlimited days (requires medical report)',
        days_allowed=0,  # Unlimited
        is_paid=True,
        requires_document=True,
        gender_specific='A',
        reset_period='NEVER'
    )
    
    # Relative Death Leave
    LeaveType.objects.create(
        name='Relative Death Leave',
        code='DEATH',
        category='SPECIAL',
        description='3 days leave for death of a relative',
        days_allowed=3,
        is_paid=True,
        requires_document=True,
        gender_specific='A',
        reset_period='EVENT'
    )
    
    # Maternity Leave
    LeaveType.objects.create(
        name='Maternity Leave',
        code='MATERNITY',
        category='SPECIAL',
        description='60 days leave for childbirth',
        days_allowed=60,
        is_paid=True,
        requires_document=True,
        gender_specific='F',
        reset_period='EVENT'
    )
    
    # Paternity Leave
    LeaveType.objects.create(
        name='Paternity Leave',
        code='PATERNITY',
        category='SPECIAL',
        description='1 day leave for childbirth',
        days_allowed=1,
        is_paid=True,
        requires_document=True,
        gender_specific='M',
        reset_period='EVENT'
    )
    
    # Marriage Leave
    LeaveType.objects.create(
        name='Marriage Leave',
        code='MARRIAGE',
        category='SPECIAL',
        description='3 days leave for marriage',
        days_allowed=3,
        is_paid=True,
        requires_document=True,
        gender_specific='A',
        reset_period='EVENT'
    )

def delete_leave_types(apps, schema_editor):
    LeaveType = apps.get_model('attendance', 'LeaveType')
    LeaveType.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0003_add_leave_management'),
    ]

    operations = [
        migrations.RunPython(create_leave_types, delete_leave_types),
    ]
