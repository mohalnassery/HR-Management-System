from django.db import migrations
from django.utils import timezone

def create_default_shifts(apps, schema_editor):
    Shift = apps.get_model('attendance', 'Shift')
    
    # Define default shifts
    default_shifts = [
        {
            'name': 'Default Shift',
            'shift_type': 'DEFAULT',
            'start_time': '07:00',
            'end_time': '16:00',
            'default_start_time': '07:00',
            'default_end_time': '16:00',
            'grace_period': 15,
            'break_duration': 60,
            'is_active': True,
        },
        {
            'name': 'Night Shift',
            'shift_type': 'NIGHT',
            'start_time': '19:00',
            'end_time': '04:00',
            'default_start_time': '19:00',
            'default_end_time': '04:00',
            'grace_period': 15,
            'break_duration': 60,
            'is_active': True,
        },
        {
            'name': 'Open Shift',
            'shift_type': 'OPEN',
            'start_time': '00:00',
            'end_time': '23:59',
            'default_start_time': '00:00',
            'default_end_time': '23:59',
            'grace_period': 30,
            'break_duration': 60,
            'is_active': True,
        },
    ]

    # Create shifts if they don't exist
    for shift_data in default_shifts:
        Shift.objects.get_or_create(
            shift_type=shift_data['shift_type'],
            defaults=shift_data
        )

def remove_default_shifts(apps, schema_editor):
    Shift = apps.get_model('attendance', 'Shift')
    Shift.objects.filter(shift_type__in=['DEFAULT', 'NIGHT', 'OPEN']).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0011_shift_ramadan_end_time_shift_ramadan_start_time'),
    ]

    operations = [
        migrations.RunPython(create_default_shifts, remove_default_shifts),
    ] 