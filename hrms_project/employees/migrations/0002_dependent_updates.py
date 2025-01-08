from django.db import migrations, models
import django.core.validators
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0009_alter_employee_nationality'),
    ]

    operations = [
        migrations.RenameField(
            model_name='employeedependent',
            old_name='relationship',
            new_name='relation',
        ),
        migrations.RenameField(
            model_name='employeedependent',
            old_name='is_sponsored',
            new_name='valid_passage',
        ),
        migrations.RemoveField(
            model_name='employeedependent',
            name='documents',
        ),
        migrations.AddField(
            model_name='employeedependent',
            name='cpr_expiry',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='employeedependent',
            name='cpr_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='employeedependent',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='employeedependent',
            name='passport_expiry',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='employeedependent',
            name='passport_number',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='employeedependent',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='employeedependent',
            name='relation',
            field=models.CharField(choices=[('spouse', 'Spouse'), ('child', 'Child'), ('parent', 'Parent'), ('sibling', 'Sibling'), ('other', 'Other')], max_length=20),
        ),
        migrations.CreateModel(
            name='DependentDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('document_type', models.CharField(choices=[('passport', 'Passport'), ('id', 'ID'), ('visa', 'Visa'), ('other', 'Other')], max_length=20)),
                ('document_number', models.CharField(blank=True, max_length=50, null=True)),
                ('document_file', models.FileField(upload_to='dependent_documents/%Y/%m/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])])),
                ('issue_date', models.DateField()),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('country_of_origin', models.CharField(max_length=100)),
                ('status', models.CharField(choices=[('valid', 'Valid'), ('expired', 'Expired')], default='valid', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('dependent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='employees.employeedependent')),
            ],
            options={
                'verbose_name': 'Dependent Document',
                'verbose_name_plural': 'Dependent Documents',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterModelOptions(
            name='employeedependent',
            options={'ordering': ['name'], 'verbose_name': 'Employee Dependent', 'verbose_name_plural': 'Employee Dependents'},
        ),
    ]
