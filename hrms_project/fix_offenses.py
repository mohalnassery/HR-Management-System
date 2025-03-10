"""
Script to fix active status for all offenses in the database.
Run this with: python fix_offenses.py
"""
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms_project.settings')
django.setup()

from employees.models import EmployeeOffence
from django.utils import timezone

def fix_offenses():
    """Fix active status for all offenses"""
    # Count offenses before update
    total_offenses = EmployeeOffence.objects.count()
    inactive_offenses = EmployeeOffence.objects.filter(is_active=False).count()
    
    print(f"Found {total_offenses} total offenses, {inactive_offenses} are currently inactive")
    
    # Update all offenses except those that are monetary with zero remaining amount
    updated = EmployeeOffence.objects.filter(
        is_active=False
    ).exclude(
        applied_penalty='MONETARY', 
        remaining_amount__lte=0
    ).update(
        is_active=True
    )
    
    print(f"Fixed {updated} offenses by setting them to active")
    
    # Now show the updated counts
    inactive_after = EmployeeOffence.objects.filter(is_active=False).count()
    print(f"After update: {inactive_after} offenses remain inactive")
    
    # Show all active offenses
    active_offenses = EmployeeOffence.objects.filter(is_active=True)
    print("\nActive offenses:")
    for offense in active_offenses:
        print(f"ID: {offense.id}, Employee: {offense.employee}, Rule: {offense.rule.name}, Date: {offense.offense_date}")

if __name__ == "__main__":
    fix_offenses()
