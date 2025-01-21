from django.db import migrations

def convert_penalty_to_code(penalty):
    penalty_map = {
        'Oral Warning': 'ORAL',
        'Written Warning': 'WRITTEN',
        '0.05': 'D005',
        '0.10': 'D010',
        '0.15': 'D015',
        '0.25': 'D025',
        '0.50': 'D050',
        '0.75': 'D075',
        '1': 'D100',
    }
    return penalty_map.get(penalty, penalty)

def add_initial_offense_rules(apps, schema_editor):
    OffenseRule = apps.get_model('employees', 'OffenseRule')
    
    # Initial offense rules data
    rules = [
        {
            'rule_id': '1.1',
            'group': 'ATTENDANCE_TIME',
            'name': 'Tardiness - Up to 15 Min (No Disruption)',
            'description': 'Reporting late up to 15 minutes beyond the attendance time without permission or a valid excuse, where the delay doesn\'t hamper other workers.',
            'first_penalty': convert_penalty_to_code('Oral Warning'),
            'second_penalty': convert_penalty_to_code('Written Warning'),
            'third_penalty': convert_penalty_to_code('0.05'),
            'fourth_penalty': convert_penalty_to_code('0.10'),
            'remarks': '',
        },
        {
            'rule_id': '1.2',
            'group': 'ATTENDANCE_TIME',
            'name': 'Tardiness - Up to 15 Min (With Disruption)',
            'description': 'Reporting late up to 15 minutes beyond the attendance time without permission or a valid excuse, resulting in the disruption of other workers.',
            'first_penalty': convert_penalty_to_code('Oral Warning'),
            'second_penalty': convert_penalty_to_code('Written Warning'),
            'third_penalty': convert_penalty_to_code('0.25'),
            'fourth_penalty': convert_penalty_to_code('0.50'),
            'remarks': '',
        },
        {
            'rule_id': '1.3',
            'group': 'ATTENDANCE_TIME',
            'name': 'Tardiness - 15 to 30 Min (No Disruption)',
            'description': 'Reporting late more than 15 minutes but up to 30 minutes beyond the attendance time without permission or valid excuse, where the delay doesn\'t hamper other workers.',
            'first_penalty': convert_penalty_to_code('Written Warning'),
            'second_penalty': convert_penalty_to_code('0.15'),
            'third_penalty': convert_penalty_to_code('0.25'),
            'fourth_penalty': convert_penalty_to_code('0.50'),
            'remarks': '',
        },
        {
            'rule_id': '1.4',
            'group': 'ATTENDANCE_TIME',
            'name': 'Tardiness - 15 to 30 Min (With Disruption)',
            'description': 'Reporting late more than 15 minutes but up to 30 minutes beyond the attendance time without permission or valid excuse, resulting in the disruption of other workers.',
            'first_penalty': convert_penalty_to_code('Written Warning'),
            'second_penalty': convert_penalty_to_code('0.50'),
            'third_penalty': convert_penalty_to_code('0.75'),
            'fourth_penalty': convert_penalty_to_code('1'),
            'remarks': '',
        },
    ]
    
    for rule_data in rules:
        OffenseRule.objects.create(**rule_data)

def remove_initial_offense_rules(apps, schema_editor):
    OffenseRule = apps.get_model('employees', 'OffenseRule')
    OffenseRule.objects.filter(rule_id__in=['1.1', '1.2', '1.3', '1.4']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('employees', '0002_add_is_active_to_offense'),
    ]

    operations = [
        migrations.RunPython(add_initial_offense_rules, remove_initial_offense_rules),
    ]
