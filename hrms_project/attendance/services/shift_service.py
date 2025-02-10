from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.models import User

from ..models import Shift, ShiftAssignment, RamadanPeriod
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
        return assignment.shift if assignment else None

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
    def get_ramadan_shift_timing(shift: Shift, date: date) -> Optional[Dict[str, Any]]:
        """
        Get adjusted shift timing if the given date falls in Ramadan period
        
        Args:
            shift: The shift to check
            date: The date to check for Ramadan timing
            
        Returns:
            Dict with adjusted start_time and end_time if in Ramadan, None otherwise
        """
        ramadan_period = RamadanPeriod.objects.filter(
            start_date__lte=date,
            end_date__gte=date,
            is_active=True
        ).first()
        
        if not ramadan_period:
            return None
            
        # Default Ramadan adjustment (reduce by 2 hours)
        start_time = shift.start_time
        end_time = (
            datetime.combine(date, shift.end_time) - timedelta(hours=2)
        ).time()
        
        return {
            'start_time': start_time,
            'end_time': end_time
        }

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
