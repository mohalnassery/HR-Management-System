import logging
from datetime import datetime, date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib.auth.models import User

from attendance.models import (
    Shift, ShiftAssignment, RamadanPeriod, AttendanceLog
)
from attendance.cache import (
    ShiftCache, RamadanCache, invalidate_department_caches,
    invalidate_employee_caches
)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Cleanup and maintenance of shift-related data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to keep in history (default: 90)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cleanup without confirmation'
        )
        parser.add_argument(
            '--archive',
            action='store_true',
            help='Archive data instead of deleting'
        )

    def handle(self, *args, **options):
        try:
            days = options['days']
            dry_run = options['dry_run']
            force = options['force']
            archive = options['archive']
            
            cutoff_date = timezone.now().date() - timedelta(days=days)
            
            self.stdout.write(
                self.style.WARNING(
                    f'\nStarting shift data cleanup for data older than {cutoff_date}'
                )
            )
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('DRY RUN - No data will be deleted')
                )
            
            # Confirm unless --force is used
            if not dry_run and not force:
                confirm = input(
                    '\nThis will permanently delete old shift data. '
                    'Are you sure? [y/N]: '
                )
                if confirm.lower() != 'y':
                    self.stdout.write('Operation cancelled.')
                    return
            
            with transaction.atomic():
                # Clean up expired shift assignments
                self.cleanup_shift_assignments(cutoff_date, dry_run, archive)
                
                # Clean up old Ramadan periods
                self.cleanup_ramadan_periods(cutoff_date, dry_run, archive)
                
                # Clean up orphaned shifts
                self.cleanup_orphaned_shifts(dry_run)
                
                # Clean up duplicate assignments
                self.cleanup_duplicate_assignments(dry_run)
                
                if not dry_run:
                    # Clear relevant caches
                    self.clear_caches()
            
            self.stdout.write(self.style.SUCCESS('\nCleanup completed successfully'))
            
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Error during cleanup: {str(e)}')
            )
            logger.error('Error in cleanup_shifts command', exc_info=True)

    def cleanup_shift_assignments(self, cutoff_date, dry_run, archive):
        """Clean up old shift assignments"""
        old_assignments = ShiftAssignment.objects.filter(
            end_date__lt=cutoff_date,
            is_active=False
        )
        
        count = old_assignments.count()
        self.stdout.write(f'\nFound {count} old shift assignments')
        
        if not dry_run:
            if archive:
                # Archive assignments before deleting
                self.archive_assignments(old_assignments)
            
            # Delete assignments
            old_assignments.delete()
            self.stdout.write(f'Deleted {count} old assignments')

    def cleanup_ramadan_periods(self, cutoff_date, dry_run, archive):
        """Clean up old Ramadan periods"""
        old_periods = RamadanPeriod.objects.filter(
            end_date__lt=cutoff_date,
            is_active=False
        )
        
        count = old_periods.count()
        self.stdout.write(f'\nFound {count} old Ramadan periods')
        
        if not dry_run:
            if archive:
                # Archive periods before deleting
                self.archive_ramadan_periods(old_periods)
            
            # Delete periods
            old_periods.delete()
            self.stdout.write(f'Deleted {count} old periods')

    def cleanup_orphaned_shifts(self, dry_run):
        """Clean up shifts with no assignments"""
        orphaned_shifts = Shift.objects.filter(
            shiftassignment__isnull=True
        )
        
        count = orphaned_shifts.count()
        self.stdout.write(f'\nFound {count} orphaned shifts')
        
        if not dry_run:
            orphaned_shifts.delete()
            self.stdout.write(f'Deleted {count} orphaned shifts')

    def cleanup_duplicate_assignments(self, dry_run):
        """Clean up duplicate active assignments for employees"""
        duplicates = ShiftAssignment.objects.filter(
            is_active=True
        ).values(
            'employee'
        ).annotate(
            count=Count('id')
        ).filter(
            count__gt=1
        )
        
        count = len(duplicates)
        self.stdout.write(f'\nFound {count} employees with multiple active assignments')
        
        if not dry_run:
            for dup in duplicates:
                # Keep only the most recent assignment
                assignments = ShiftAssignment.objects.filter(
                    employee_id=dup['employee'],
                    is_active=True
                ).order_by('-created_at')
                
                # Deactivate all but the most recent
                assignments.exclude(id=assignments[0].id).update(is_active=False)
            
            self.stdout.write(f'Fixed {count} duplicate assignments')

    def archive_assignments(self, assignments):
        """Archive shift assignments to file"""
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'shift_assignments_archive_{timestamp}.csv'
        
        with open(filename, 'w') as f:
            # Write header
            f.write('employee_id,shift_id,start_date,end_date,created_at\n')
            
            # Write data
            for assignment in assignments:
                f.write(
                    f'{assignment.employee_id},{assignment.shift_id},'
                    f'{assignment.start_date},{assignment.end_date},'
                    f'{assignment.created_at}\n'
                )
        
        self.stdout.write(f'Archived assignments to {filename}')

    def archive_ramadan_periods(self, periods):
        """Archive Ramadan periods to file"""
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'ramadan_periods_archive_{timestamp}.csv'
        
        with open(filename, 'w') as f:
            # Write header
            f.write('year,start_date,end_date,is_active\n')
            
            # Write data
            for period in periods:
                f.write(
                    f'{period.year},{period.start_date},'
                    f'{period.end_date},{period.is_active}\n'
                )
        
        self.stdout.write(f'Archived Ramadan periods to {filename}')

    def clear_caches(self):
        """Clear all related caches"""
        RamadanCache.clear_all_periods()
        
        # Clear department caches
        departments = set(ShiftAssignment.objects.values_list(
            'employee__department_id',
            flat=True
        ))
        for dept_id in departments:
            if dept_id:
                invalidate_department_caches(dept_id)
        
        self.stdout.write('Cleared relevant caches')
