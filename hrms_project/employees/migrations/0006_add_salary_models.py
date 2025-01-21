from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('employees', '0005_remove_employeeoffence_acknowledgment_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SalaryDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('basic_salary', models.DecimalField(decimal_places=3, max_digits=10)),
                ('housing_allowance', models.DecimalField(decimal_places=3, default=0, max_digits=10)),
                ('transportation_allowance', models.DecimalField(decimal_places=3, default=0, max_digits=10)),
                ('other_allowances', models.JSONField(default=dict, help_text='Store other allowances as key-value pairs')),
                ('total_salary', models.DecimalField(decimal_places=3, max_digits=10)),
                ('currency', models.CharField(default='BHD', max_length=3)),
                ('effective_from', models.DateField()),
                ('effective_to', models.DateField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_salary_details', to=settings.AUTH_USER_MODEL)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='salary_details', to='employees.employee')),
            ],
            options={
                'verbose_name': 'Salary Detail',
                'verbose_name_plural': 'Salary Details',
                'ordering': ['-effective_from'],
            },
        ),
        migrations.CreateModel(
            name='SalaryCertificate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('certificate_number', models.CharField(max_length=50, unique=True)),
                ('issued_date', models.DateField()),
                ('purpose', models.CharField(max_length=200)),
                ('is_valid', models.BooleanField(default=True)),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('additional_notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='salary_certificates', to='employees.employee')),
                ('issued_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('salary_detail', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='employees.salarydetail')),
            ],
            options={
                'verbose_name': 'Salary Certificate',
                'verbose_name_plural': 'Salary Certificates',
                'ordering': ['-issued_date'],
            },
        ),
        migrations.CreateModel(
            name='SalaryRevision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('revision_type', models.CharField(choices=[('INC', 'Increment'), ('PRO', 'Promotion'), ('ADJ', 'Adjustment'), ('DEM', 'Demotion'), ('PEN', 'Penalty'), ('OTH', 'Other')], max_length=3)),
                ('revision_date', models.DateField()),
                ('reason', models.TextField()),
                ('reference_number', models.CharField(blank=True, max_length=50, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='salary_revisions', to='employees.employee')),
                ('new_salary', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='revisions_to', to='employees.salarydetail')),
                ('previous_salary', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='revisions_from', to='employees.salarydetail')),
            ],
            options={
                'verbose_name': 'Salary Revision',
                'verbose_name_plural': 'Salary Revisions',
                'ordering': ['-revision_date'],
            },
        ),
    ]