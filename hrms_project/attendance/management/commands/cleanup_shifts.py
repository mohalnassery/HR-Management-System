import logging
from datetime import datetime, date, timedelta
from typing import Optional, Callable, Any, List, Dict
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count, QuerySet, Model
from django.contrib.auth.models import User

from attendance.models import (
    Shift, ShiftAssignment, RamadanPeriod, AttendanceLog
)
from attendance.cache import (
    ShiftCache, RamadanCache, invalidate_department_caches,
    invalidate_employee_caches
)

logger = logging.getLogger(__name__)

class CacheInvalidationService:
    """Service for handling cache invalidation operations"""
    
    @staticmethod
    def clear_all_caches(command_instance: BaseCommand) -> None:
        """Clear all relevant caches"""
        # Clear Ramadan periods
        RamadanCache.clear_all_periods()
        
        # Get unique departments from shift assignments
        departments = set(ShiftAssignment.objects.values_list(
            'employee__department_id',
            flat=True
        ))
        
        # Clear department caches
        for dept_id in departments:
            if dept_id:
                invalidate_department_caches(dept_id)
        
        command_instance.stdout.write('Cleared relevant caches')

class DataArchiver:
    """Handles archiving data to CSV files"""
    
    @staticmethod
    def archive_to_csv(
        queryset: QuerySet,
        fields: List[str],
        filename_prefix: str,
        command_instance: BaseCommand
    ) -> None:
        """
        Archive queryset data to a CSV file.
        
        Args:
            queryset: The queryset to archive
            fields: List of field names to include
            filename_prefix: Prefix for the archive filename
            command_instance: Command instance for output
        """
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{filename_prefix}_{timestamp}.csv'
        
        with open(filename, 'w') as f:
            # Write header
            f.write(','.join(fields) + '\n')
            
            # Write data
            for obj in queryset:
                values = [str(getattr(obj, field)) for field in fields]
                f.write(','.join(values) + '\n')
        
        command_instance.stdout.write(f'Archived data to {filename}')

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
                self._cleanup_objects(
                    queryset=ShiftAssignment.objects.filter(
                        end_date__lt=cutoff_date,
                        is_active=False
                    ),
                    object_type='shift assignments',
                    archive_config={
                        'fields': ['employee_id', 'shift_id', 'start_date', 'end_date', 'created_at'],
                        'prefix': 'shift_assignments_archive'
                    } if archive else None,
                    dry_run=dry_run
                )
                
                # Clean up old Ramadan periods
                self._cleanup_objects(
                    queryset=RamadanPeriod.objects.filter(
                        end_date__lt=cutoff_date,
                        is_active=False
                    ),
                    object_type='Ramadan periods',
                    archive_config={
                        'fields': ['year', 'start_date', 'end_date', 'is_active'],
                        'prefix': 'ramadan_periods_archive'
                    } if archive else None,
                    dry_run=dry_run
                )
                
                # Clean up orphaned shifts
                self._cleanup_objects(
                    queryset=Shift.objects.filter(shiftassignment__isnull=True),
                    object_type='orphaned shifts',
                    dry_run=dry_run
                )
                
                # Clean up duplicate assignments
                self._cleanup_duplicate_assignments(dry_run)
                
                if not dry_run:
                    # Clear relevant caches
                    CacheInvalidationService.clear_all_caches(self)
            
            self.stdout.write(self.style.SUCCESS('\nCleanup completed successfully'))
            
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Error during cleanup: {str(e)}')
            )
            logger.error('Error in cleanup_shifts command', exc_info=True)

    def _cleanup_objects(
        self,
        queryset: QuerySet,
        object_type: str,
        archive_config: Optional[Dict[str, Any]] = None,
        dry_run: bool = False
    ) -> None:
        """
        Generic cleanup function for handling object deletion and archiving.
        
        Args:
            queryset: The queryset to clean up
            object_type: Description of the object type for logging
            archive_config: Optional archive configuration with fields and filename prefix
            dry_run: Whether this is a dry run
        """
        count = queryset.count()
        self.stdout.write(f'\nFound {count} {object_type}')
        
        if not dry_run:
            if archive_config:
                DataArchiver.archive_to_csv(
                    queryset,
                    archive_config['fields'],
                    archive_config['prefix'],
                    self
                )
            
            queryset.delete()
            self.stdout.write(f'Deleted {count} {object_type}')

    def _cleanup_duplicate_assignments(self, dry_run: bool) -> None:
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
