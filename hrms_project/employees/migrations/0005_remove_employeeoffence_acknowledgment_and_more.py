# Generated by Django 4.2.9 on 2025-01-12 07:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0004_update_offense_groups'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employeeoffence',
            name='acknowledgment',
        ),
        migrations.RemoveField(
            model_name='employeeoffence',
            name='warning_letter',
        ),
        migrations.AddField(
            model_name='employeeoffence',
            name='completed_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='employeeoffence',
            name='monetary_amount',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='employeeoffence',
            name='monthly_deduction',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='employeeoffence',
            name='refused_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='employeeoffence',
            name='refused_reason',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='employeeoffence',
            name='remaining_amount',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='employeeoffence',
            name='sent_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='employeeoffence',
            name='signed_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='employeeoffence',
            name='applied_penalty',
            field=models.CharField(choices=[('ORAL', 'Oral Warning'), ('WRITTEN', 'Written Warning'), ('D005', '0.05 Day Deduction'), ('D010', '0.10 Day Deduction'), ('D015', '0.15 Day Deduction'), ('D025', '0.25 Day Deduction'), ('D030', '0.30 Day Deduction'), ('D050', '0.50 Day Deduction'), ('D075', '0.75 Day Deduction'), ('D100', '1 Day Deduction'), ('D200', '2 Days Deduction'), ('D300', '3 Days Deduction'), ('D500', '5 Days Deduction'), ('MONETARY', 'Monetary Penalty'), ('DISMISS', 'Dismissal')], max_length=10),
        ),
        migrations.AlterField(
            model_name='employeeoffence',
            name='original_penalty',
            field=models.CharField(choices=[('ORAL', 'Oral Warning'), ('WRITTEN', 'Written Warning'), ('D005', '0.05 Day Deduction'), ('D010', '0.10 Day Deduction'), ('D015', '0.15 Day Deduction'), ('D025', '0.25 Day Deduction'), ('D030', '0.30 Day Deduction'), ('D050', '0.50 Day Deduction'), ('D075', '0.75 Day Deduction'), ('D100', '1 Day Deduction'), ('D200', '2 Days Deduction'), ('D300', '3 Days Deduction'), ('D500', '5 Days Deduction'), ('MONETARY', 'Monetary Penalty'), ('DISMISS', 'Dismissal')], max_length=10),
        ),
        migrations.AlterField(
            model_name='offenserule',
            name='first_penalty',
            field=models.CharField(choices=[('ORAL', 'Oral Warning'), ('WRITTEN', 'Written Warning'), ('D005', '0.05 Day Deduction'), ('D010', '0.10 Day Deduction'), ('D015', '0.15 Day Deduction'), ('D025', '0.25 Day Deduction'), ('D030', '0.30 Day Deduction'), ('D050', '0.50 Day Deduction'), ('D075', '0.75 Day Deduction'), ('D100', '1 Day Deduction'), ('D200', '2 Days Deduction'), ('D300', '3 Days Deduction'), ('D500', '5 Days Deduction'), ('MONETARY', 'Monetary Penalty'), ('DISMISS', 'Dismissal')], max_length=10),
        ),
        migrations.AlterField(
            model_name='offenserule',
            name='fourth_penalty',
            field=models.CharField(choices=[('ORAL', 'Oral Warning'), ('WRITTEN', 'Written Warning'), ('D005', '0.05 Day Deduction'), ('D010', '0.10 Day Deduction'), ('D015', '0.15 Day Deduction'), ('D025', '0.25 Day Deduction'), ('D030', '0.30 Day Deduction'), ('D050', '0.50 Day Deduction'), ('D075', '0.75 Day Deduction'), ('D100', '1 Day Deduction'), ('D200', '2 Days Deduction'), ('D300', '3 Days Deduction'), ('D500', '5 Days Deduction'), ('MONETARY', 'Monetary Penalty'), ('DISMISS', 'Dismissal')], max_length=10),
        ),
        migrations.AlterField(
            model_name='offenserule',
            name='second_penalty',
            field=models.CharField(choices=[('ORAL', 'Oral Warning'), ('WRITTEN', 'Written Warning'), ('D005', '0.05 Day Deduction'), ('D010', '0.10 Day Deduction'), ('D015', '0.15 Day Deduction'), ('D025', '0.25 Day Deduction'), ('D030', '0.30 Day Deduction'), ('D050', '0.50 Day Deduction'), ('D075', '0.75 Day Deduction'), ('D100', '1 Day Deduction'), ('D200', '2 Days Deduction'), ('D300', '3 Days Deduction'), ('D500', '5 Days Deduction'), ('MONETARY', 'Monetary Penalty'), ('DISMISS', 'Dismissal')], max_length=10),
        ),
        migrations.AlterField(
            model_name='offenserule',
            name='third_penalty',
            field=models.CharField(choices=[('ORAL', 'Oral Warning'), ('WRITTEN', 'Written Warning'), ('D005', '0.05 Day Deduction'), ('D010', '0.10 Day Deduction'), ('D015', '0.15 Day Deduction'), ('D025', '0.25 Day Deduction'), ('D030', '0.30 Day Deduction'), ('D050', '0.50 Day Deduction'), ('D075', '0.75 Day Deduction'), ('D100', '1 Day Deduction'), ('D200', '2 Days Deduction'), ('D300', '3 Days Deduction'), ('D500', '5 Days Deduction'), ('MONETARY', 'Monetary Penalty'), ('DISMISS', 'Dismissal')], max_length=10),
        ),
    ]
