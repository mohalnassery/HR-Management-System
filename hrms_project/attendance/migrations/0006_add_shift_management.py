from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0010_employee_user'),
        ('core', '0001_initial'),  
        ('attendance', '0004_attendancelog_early_departure_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='shift',
            name='shift_type',
            field=models.CharField(
                choices=[
                    ('DEFAULT', 'Default Shift (7AM-4PM)'),
                    ('CLEANER', 'Cleaner Shift (6AM-3PM)'),
                    ('NIGHT', 'Night Shift'),
                    ('OPEN', 'Open Shift'),
                ],
                default='DEFAULT',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='shift',
            name='grace_period',
            field=models.PositiveIntegerField(
                default=15,
                help_text='Grace period in minutes'
            ),
        ),
        migrations.AddField(
            model_name='shift',
            name='break_duration',
            field=models.PositiveIntegerField(
                default=60,
                help_text='Break duration in minutes'
            ),
        ),
        migrations.CreateModel(
            name='RamadanPeriod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Ramadan Period',
                'verbose_name_plural': 'Ramadan Periods',
                'ordering': ['-year'],
            },
        ),
        migrations.CreateModel(
            name='ShiftAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(help_text='Start date of shift assignment')),
                ('end_date', models.DateField(blank=True, help_text='End date of shift assignment (null = permanent)', null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_shift_assignments', to='core.user')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shift_assignments', to='employees.employee')),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='attendance.shift')),
            ],
            options={
                'verbose_name': 'Shift Assignment',
                'verbose_name_plural': 'Shift Assignments',
                'ordering': ['-start_date'],
            },
        ),
    ]
