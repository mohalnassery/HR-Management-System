# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0016_attendancelog_holiday_holiday_applicable_departments_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='holiday',
            name='applicable_departments',
        ),
        migrations.RemoveField(
            model_name='attendancelog',
            name='holiday',
        ),
    ]
