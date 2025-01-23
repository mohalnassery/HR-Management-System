from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
from django.utils import timezone

def migrate_attendance_data(apps, schema_editor):
    """
    Migrate data from AttendanceRecord, AttendanceLog, and AttendanceEdit to new Attendance model
    """
    # Get the old and new model classes
    AttendanceRecord = apps.get_model('attendance', 'AttendanceRecord')
    AttendanceLog = apps.get_model('attendance', 'AttendanceLog')
    AttendanceEdit = apps.get_model('attendance', 'AttendanceEdit')
    Attendance = apps.get_model('attendance', 'Attendance')
    
    # Process each attendance log
    for log in AttendanceLog.objects.all():
        # Create new attendance record
        attendance = Attendance.objects.create(
            employee=log.employee,
            date=log.date,
            first_in_time=log.first_in_time,
            last_out_time=log.last_out_time,
            shift=log.shift,
            source=log.source,
            is_active=log.is_active,
            created_at=log.created_at,
            created_by=log.created_by,
            timestamp=timezone.datetime.combine(log.date, log.first_in_time) if log.first_in_time else None
        )
        
        # Get the edit record if it exists
        try:
            edit = AttendanceEdit.objects.get(attendance_log=log)
            attendance.original_first_in = edit.original_first_in
            attendance.original_last_out = edit.original_last_out
            attendance.edited_by = edit.edited_by
            attendance.edit_timestamp = edit.edit_timestamp
            attendance.edit_reason = edit.edit_reason
            attendance.save()
        except AttendanceEdit.DoesNotExist:
            pass
            
        # Get matching raw records
        records = AttendanceRecord.objects.filter(
            employee=log.employee,
            timestamp__date=log.date
        )
        if records.exists():
            first_record = records.order_by('timestamp').first()
            attendance.device_name = first_record.device_name
            attendance.event_point = first_record.event_point
            attendance.verify_type = first_record.verify_type
            attendance.event_description = first_record.event_description
            attendance.save()

class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('employees', '0001_initial'),
        ('attendance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('date', models.DateField()),
                ('first_in_time', models.TimeField()),
                ('last_out_time', models.TimeField()),
                ('original_first_in', models.TimeField(blank=True, null=True)),
                ('original_last_out', models.TimeField(blank=True, null=True)),
                ('device_name', models.CharField(blank=True, max_length=100, null=True)),
                ('event_point', models.CharField(blank=True, max_length=100, null=True)),
                ('verify_type', models.CharField(blank=True, max_length=50, null=True)),
                ('event_description', models.TextField(blank=True, null=True)),
                ('source', models.CharField(choices=[('system', 'System'), ('manual', 'Manual'), ('machine', 'Machine')], default='machine', max_length=20)),
                ('edit_timestamp', models.DateTimeField(blank=True, null=True)),
                ('edit_reason', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_attendance', to=settings.AUTH_USER_MODEL)),
                ('edited_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='edited_attendance', to=settings.AUTH_USER_MODEL)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance', to='employees.employee')),
                ('shift', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='attendance.shift')),
            ],
            options={
                'ordering': ['-timestamp'],
                'unique_together': {('employee', 'timestamp')},
            },
        ),
        migrations.RunPython(migrate_attendance_data),
        migrations.RemoveField(
            model_name='attendanceedit',
            name='attendance_log',
        ),
        migrations.RemoveField(
            model_name='attendanceedit',
            name='edited_by',
        ),
        migrations.RemoveField(
            model_name='attendancelog',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='attendancelog',
            name='employee',
        ),
        migrations.RemoveField(
            model_name='attendancelog',
            name='shift',
        ),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='employee',
        ),
        migrations.DeleteModel(
            name='AttendanceEdit',
        ),
        migrations.DeleteModel(
            name='AttendanceLog',
        ),
        migrations.DeleteModel(
            name='AttendanceRecord',
        ),
    ]
