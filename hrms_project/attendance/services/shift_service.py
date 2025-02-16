from datetime import datetime, date, timedelta, time
from typing import Optional, List, Dict, Any

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.models import User

from ..models import Shift, ShiftAssignment, RamadanPeriod, DateSpecificShift
from employees.models import Employee

class ShiftService:
    @staticmethod
    def get_active_shifts():
        """Get all active shifts ordered by start time"""
        return Shift.objects.filter(is_active=True).order_by('start_time')

    @staticmethod
    def get_employee_current_shift(employee: Employee) -> Optional[Shift]:
        """Get an employee's currently active shift"""
        today = timezone.now().date()
        assignment = ShiftAssignment.objects.filter(
            employee=employee,
            start_date__lte=today,
            is_active=True
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=today)
        ).first()
        if assignment:
            return assignment.shift
        
        # Fallback to default shift if no assignment
        return Shift.objects.filter(
            shift_type='DEFAULT',
            is_active=True
        ).first()

    @staticmethod
    def get_employee_shift_history(employee: Employee) -> List[Dict[str, Any]]:
        """Get complete shift assignment history for an employee"""
        assignments = ShiftAssignment.objects.filter(
            employee=employee
        ).select_related('shift', 'created_by').order_by('-start_date')
        
        return [{
            'shift_name': assignment.shift.name,
            'start_date': assignment.start_date,
            'end_date': assignment.end_date,
            'is_active': assignment.is_active,
            'created_by': assignment.created_by.get_full_name(),
            'created_at': assignment.created_at
        } for assignment in assignments]

    @staticmethod
    @transaction.atomic
    def assign_shift(
        employee: Employee,
        shift: Shift,
        start_date: date,
        end_date: Optional[date],
        created_by: User,
        is_active: bool = True
    ) -> ShiftAssignment:
        """
        Assign a shift to an employee
        
        Args:
            employee: The employee to assign the shift to
            shift: The shift to assign
            start_date: When the assignment starts
            end_date: Optional end date for temporary assignments
            created_by: User creating the assignment
            is_active: Whether the assignment should be active
            
        Returns:
            The created shift assignment
        """
        if is_active:
            # Deactivate any existing active assignments
            ShiftAssignment.objects.filter(
                employee=employee,
                is_active=True
            ).update(is_active=False)
            
        # Create new assignment
        return ShiftAssignment.objects.create(
            employee=employee,
            shift=shift,
            start_date=start_date,
            end_date=end_date,
            created_by=created_by,
            is_active=is_active
        )

    @staticmethod
    def get_shift_timing(shift: Shift, date: date) -> Dict[str, Any]:
        """
        Get shift timing for a given date considering:
        1. Date-specific shifts
        2. Default shift timings
        3. Ramadan adjustments
        
        Args:
            shift: The shift to check
            date: The date to check timing for
            
        Returns:
            Dict with start_time and end_time
        """
        # Check for date-specific shift first
        date_specific = DateSpecificShift.objects.filter(shift=shift, date=date).first()
        if date_specific:
            return {
                'start_time': date_specific.start_time,
                'end_time': date_specific.end_time,
                'is_date_specific': True
            }

        # Check for Ramadan period
        ramadan_period = RamadanPeriod.objects.filter(
            start_date__lte=date,
            end_date__gte=date,
            is_active=True
        ).first()

        # Use ramadan timing if available and we're in ramadan period
        if ramadan_period and hasattr(shift, 'ramadan_start_time') and hasattr(shift, 'ramadan_end_time'):
            if shift.ramadan_start_time and shift.ramadan_end_time:
                return {
                    'start_time': shift.ramadan_start_time,
                    'end_time': shift.ramadan_end_time,
                    'is_ramadan': True
                }

        # Return default timing
        return {
            'start_time': shift.start_time,
            'end_time': shift.end_time,
            'is_default': True
        }

    @staticmethod
    @transaction.atomic
    def set_date_specific_shift(
        shift: Shift,
        date: date,
        start_time: time,
        end_time: time,
        created_by: User
    ) -> DateSpecificShift:
        """
        Set date-specific timing for a shift
        
        Args:
            shift: The shift to set timing for
            date: The specific date
            start_time: New start time
            end_time: New end time
            created_by: User creating the override
            
        Returns:
            Created DateSpecificShift instance
        """
        date_specific, created = DateSpecificShift.objects.update_or_create(
            shift=shift,
            date=date,
            defaults={
                'start_time': start_time,
                'end_time': end_time,
                'created_by': created_by
            }
        )
        return date_specific

    @staticmethod
    def filter_assignments(
        department_id: Optional[int] = None,
        shift_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search_query: Optional[str] = None,
        assignment_type: Optional[str] = None
    ):
        """
        Filter shift assignments based on various criteria
        
        Args:
            department_id: Filter by department
            shift_id: Filter by shift
            is_active: Filter by active status
            search_query: Search employee name or number
            assignment_type: Filter by permanent/temporary
            
        Returns:
            Filtered queryset of ShiftAssignment objects
        """
        queryset = ShiftAssignment.objects.all()
        
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
            
        if shift_id:
            queryset = queryset.filter(shift_id=shift_id)
            
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
            
        if search_query:
            queryset = queryset.filter(
                Q(employee__first_name__icontains=search_query) |
                Q(employee__last_name__icontains=search_query) |
                Q(employee__employee_number__icontains=search_query)
            )
            
        if assignment_type:
            if assignment_type == 'permanent':
                queryset = queryset.filter(end_date__isnull=True)
            elif assignment_type == 'temporary':
                queryset = queryset.filter(end_date__isnull=False)
                
        return queryset.select_related(
            'employee',
            'employee__department',
            'shift',
            'created_by'
        ).order_by('-created_at')

    @staticmethod
    def get_department_shifts(department_id: int, date: Optional[date] = None) -> Dict[str, List[Dict]]:
        """
        Get all shift assignments for a department grouped by shift
        
        Args:
            department_id: The department to get shifts for
            date: Optional date to check assignments for
            
        Returns:
            Dict with shift names as keys and lists of employees as values
        """
        if not date:
            date = timezone.now().date()
            
        assignments = ShiftAssignment.objects.filter(
            employee__department_id=department_id,
            start_date__lte=date,
            is_active=True
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=date)
        ).select_related('employee', 'shift')
        
        shifts = {}
        for assignment in assignments:
            shift_name = assignment.shift.name
            if shift_name not in shifts:
                shifts[shift_name] = []
                
            shifts[shift_name].append({
                'employee_number': assignment.employee.employee_number,
                'employee_name': assignment.employee.get_full_name(),
                'assignment_id': assignment.id,
                'start_date': assignment.start_date,
                'end_date': assignment.end_date
            })
            
        return shifts

    @staticmethod
    @transaction.atomic
    def bulk_assign_shift(
        employee_ids: List[int],
        shift: Shift,
        start_date: date,
        end_date: Optional[date],
        created_by: User,
        is_active: bool = True
    ) -> int:
        """
        Assign a shift to multiple employees at once
        
        Args:
            employee_ids: List of employee IDs to assign the shift to
            shift: The shift to assign
            start_date: When the assignment starts
            end_date: Optional end date for temporary assignments
            created_by: User creating the assignments
            is_active: Whether the assignments should be active
            
        Returns:
            Number of assignments created
        """
        if is_active:
            # Deactivate existing active assignments for these employees
            ShiftAssignment.objects.filter(
                employee_id__in=employee_ids,
                is_active=True
            ).update(is_active=False)
            
        # Create new assignments
        assignments = [
            ShiftAssignment(
                employee_id=emp_id,
                shift=shift,
                start_date=start_date,
                end_date=end_date,
                created_by=created_by,
                is_active=is_active
            )
            for emp_id in employee_ids
        ]
        
        created = ShiftAssignment.objects.bulk_create(assignments)
        return len(created)
