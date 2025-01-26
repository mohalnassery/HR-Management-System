from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('employees', '0006_add_salary_models'),
    ]

    operations = [
        TrigramExtension(),
    ]
