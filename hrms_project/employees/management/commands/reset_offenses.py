from django.core.management.base import BaseCommand
from django.utils import timezone
from employees.models import EmployeeOffence


class Command(BaseCommand):
    help = 'Deactivate all offenses from previous years'

    def handle(self, *args, **kwargs):
        current_year = timezone.now().year
        count = EmployeeOffence.objects.filter(
            offense_date__year__lt=current_year,
            is_active=True
        ).count()
        
        if count > 0:
            EmployeeOffence.deactivate_previous_year_offenses()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deactivated {count} offenses from previous years')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('No previous year offenses to deactivate')
            )
