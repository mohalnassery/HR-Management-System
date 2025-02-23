from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Callable, TypeVar
from django.db.models import Count, Q
from django.core.cache import cache
from django.utils import timezone
from functools import wraps
import logging

from ..models import (
    AttendanceLog, Leave, Holiday, LeaveType
)
from employees.models import Employee, Department
from ..cache import generate_cache_key

logger = logging.getLogger('attendance')

T = TypeVar('T', bound=Dict[str, Any])

class ReportService:
    """Service class for generating various attendance reports"""
    
    CACHE_TIMEOUT = 3600  # 1 hour cache timeout
    
    @classmethod
    def _get_cache_key(cls, report_type: str, **params) -> str:
        """Generate a cache key based on report type and parameters"""
        # Convert params to a sorted tuple of values for consistent cache keys
        param_values = []
        for key in sorted(params.keys()):
            value = params[key]
            if isinstance(value, (list, tuple)):
                # Sort lists/tuples for consistent cache keys
                value = tuple(sorted(value))
            param_values.append(value)
        
        return generate_cache_key(f'report_{report_type}', *param_values)

    @classmethod
    def _generate_report(
        cls,
        report_type: str,
        data_generator: Callable[..., T],
        params: Dict[str, Any]
    ) -> T:
        """
        Base report generation function with caching.
        
        Args:
            report_type: Type of report being generated
            data_generator: Function that generates the report data
            params: Parameters for report generation
            
        Returns:
            Generated report data
        """
        logger.debug(f"Generating {report_type} report with params: {params}")
        
        try:
            # Check cache first
            cache_key = cls._get_cache_key(report_type, **params)
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug("Returning cached report data")
                return cached_data

            # Generate report data
            report_data = data_generator(**params)
            logger.debug("Successfully generated report data")

            # Add common fields
            report_data.update({
                'start_date': params['start_date'],
                'end_date': params['end_date'],
                'generated_at': timezone.now()
            })

            # Cache the report
            cache.set(cache_key, report_data, cls.CACHE_TIMEOUT)
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating report data: {str(e)}")
            raise

    @classmethod
    def _generate_attendance_data(
        cls,
        start_date: datetime,
        end_date: datetime,
        departments: Optional[List[int]] = None,
        employees: Optional[List[int]] = None,
        status: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate attendance report data"""
        # Convert datetime to date for database queries
        start_date = start_date.date()
        end_date = end_date.date()
        
        # Build base query for employees
        base_query = Employee.objects.all()
        if departments:
            base_query = base_query.filter(department_id__in=departments)
        if employees:
            base_query = base_query.filter(id__in=employees)

        # Get holidays
        holidays = Holiday.objects.filter(
            date__range=[start_date, end_date],
            is_active=True
        )
        holiday_dates = set(h.date for h in holidays)

        # Get attendance logs
        attendance_logs = AttendanceLog.objects.filter(
            date__range=[start_date, end_date]
        )
        holiday_logs = attendance_logs.filter(date__in=holiday_dates)
        non_holiday_logs = attendance_logs.exclude(date__in=holiday_dates)

        # Calculate statistics
        present_count = (
            non_holiday_logs.filter(first_in_time__isnull=False, is_late=False).count() +
            holiday_logs.filter(first_in_time__isnull=False).count()
        )
        late_count = non_holiday_logs.filter(is_late=True).count()
        absent_count = non_holiday_logs.filter(first_in_time__isnull=True).count()
        leave_count = Leave.objects.filter(
            Q(start_date__lte=end_date) & 
            Q(end_date__gte=start_date) &
            Q(status='approved')
        ).count()

        # Generate trend data
        trend_data = cls._generate_trend_data(
            start_date, end_date, attendance_logs, holidays, holiday_dates
        )

        # Generate department statistics
        department_stats = cls._generate_department_stats(
            holiday_logs, non_holiday_logs, start_date, end_date
        )

        # Generate employee records
        employee_records = cls._generate_employee_records(
            base_query, holiday_logs, non_holiday_logs, start_date, end_date
        )

        return {
            'summary': {
                'present': present_count,
                'absent': absent_count,
                'late': late_count,
                'leave': leave_count
            },
            'trend_data': trend_data,
            'department_stats': department_stats,
            'employee_records': employee_records,
            'holidays': [
                {
                    'date': h.date.strftime('%Y-%m-%d'),
                    'name': h.name,
                    'description': h.description if hasattr(h, 'description') else ''
                }
                for h in holidays
            ]
        }

    @classmethod
    def _generate_leave_data(
        cls,
        start_date: datetime,
        end_date: datetime,
        departments: Optional[List[int]] = None,
        employees: Optional[List[int]] = None,
        leave_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate leave report data"""
        # Convert datetime to date for database queries
        start_date = start_date.date()
        end_date = end_date.date()
        
        # Build base query
        leaves = Leave.objects.filter(
            Q(start_date__lte=end_date) & 
            Q(end_date__gte=start_date)
        )
        
        if departments:
            leaves = leaves.filter(employee__department_id__in=departments)
        if employees:
            leaves = leaves.filter(employee_id__in=employees)
        if leave_types:
            leaves = leaves.filter(leave_type__name__in=leave_types)

        # Calculate statistics
        total_leaves = leaves.count()
        approved_leaves = leaves.filter(status='approved').count()
        pending_leaves = leaves.filter(status='pending').count()
        rejected_leaves = leaves.filter(status='rejected').count()

        # Generate leave type statistics
        leave_type_stats = cls._generate_leave_type_stats(leaves)

        # Generate department statistics
        department_stats = cls._generate_leave_department_stats(leaves)

        # Generate employee records
        employee_records = [
            {
                'employee_name': f"{leave.employee.first_name} {leave.employee.last_name}",
                'department': leave.employee.department.name if leave.employee.department else '-',
                'leave_type': leave.leave_type.name,
                'start_date': leave.start_date,
                'end_date': leave.end_date,
                'duration': (leave.end_date - leave.start_date).days + 1,
                'status': leave.status
            }
            for leave in leaves
        ]

        return {
            'total_leaves': total_leaves,
            'approved_leaves': approved_leaves,
            'pending_leaves': pending_leaves,
            'rejected_leaves': rejected_leaves,
            'leave_type_stats': leave_type_stats,
            'department_stats': department_stats,
            'employee_records': employee_records
        }

    @classmethod
    def _generate_holiday_data(
        cls,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate holiday report data"""
        # Convert datetime to date for database queries
        start_date = start_date.date()
        end_date = end_date.date()
        
        holidays = Holiday.objects.filter(
            date__range=[start_date, end_date],
            is_active=True
        ).order_by('date')

        # Generate monthly distribution
        months = {}
        for holiday in holidays:
            month = holiday.date.strftime('%B %Y')
            if month not in months:
                months[month] = {
                    'name': month,
                    'count': 0,
                    'holidays': []
                }
            months[month]['count'] += 1
            months[month]['holidays'].append({
                'date': holiday.date,
                'name': holiday.name
            })

        return {
            'total_holidays': holidays.count(),
            'holidays': [
                {
                    'date': h.date,
                    'name': h.name,
                    'description': h.description if hasattr(h, 'description') else ''
                }
                for h in holidays
            ],
            'monthly_distribution': list(months.values())
        }

    @classmethod
    def get_attendance_report(
        cls,
        start_date: datetime,
        end_date: datetime,
        departments: Optional[List[int]] = None,
        employees: Optional[List[int]] = None,
        status: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate attendance report for the given parameters"""
        return cls._generate_report(
            'attendance',
            cls._generate_attendance_data,
            {
                'start_date': start_date,
                'end_date': end_date,
                'departments': departments,
                'employees': employees,
                'status': status
            }
        )

    @classmethod
    def get_leave_report(
        cls,
        start_date: datetime,
        end_date: datetime,
        departments: Optional[List[int]] = None,
        employees: Optional[List[int]] = None,
        leave_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate leave report for the given parameters"""
        return cls._generate_report(
            'leave',
            cls._generate_leave_data,
            {
                'start_date': start_date,
                'end_date': end_date,
                'departments': departments,
                'employees': employees,
                'leave_types': leave_types
            }
        )

    @classmethod
    def get_holiday_report(
        cls,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate holiday report for the given date range"""
        return cls._generate_report(
            'holiday',
            cls._generate_holiday_data,
            {
                'start_date': start_date,
                'end_date': end_date
            }
        )

    # Helper methods for generating report components
    @staticmethod
    def _generate_trend_data(
        start_date: datetime,
        end_date: datetime,
        attendance_logs: Any,
        holidays: Any,
        holiday_dates: set
    ) -> List[Dict[str, Any]]:
        """Generate daily trend data"""
        trend_data = []
        current_date = start_date
        while current_date <= end_date:
            day_logs = attendance_logs.filter(date=current_date)
            is_holiday = current_date in holiday_dates
            holiday_obj = holidays.filter(date=current_date).first() if is_holiday else None
            
            if is_holiday:
                trend_data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'present': day_logs.filter(first_in_time__isnull=False).count(),
                    'absent': 0,  # Don't count absences on holidays
                    'late': 0,    # Don't count late on holidays
                    'leave': Leave.objects.filter(
                        Q(start_date__lte=current_date) & 
                        Q(end_date__gte=current_date) &
                        Q(status='approved')
                    ).count(),
                    'is_holiday': True,
                    'holiday_name': holiday_obj.name if holiday_obj else 'Holiday'
                })
            else:
                trend_data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'present': day_logs.filter(first_in_time__isnull=False, is_late=False).count(),
                    'absent': day_logs.filter(first_in_time__isnull=True).count(),
                    'late': day_logs.filter(is_late=True).count(),
                    'leave': Leave.objects.filter(
                        Q(start_date__lte=current_date) & 
                        Q(end_date__gte=current_date) &
                        Q(status='approved')
                    ).count(),
                    'is_holiday': False,
                    'holiday_name': None
                })
            current_date += timedelta(days=1)
        return trend_data

    @staticmethod
    def _generate_department_stats(
        holiday_logs: Any,
        non_holiday_logs: Any,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Generate department statistics"""
        department_stats = []
        for dept in Department.objects.all():
            dept_holiday_logs = holiday_logs.filter(employee__department=dept)
            dept_non_holiday_logs = non_holiday_logs.filter(employee__department=dept)
            
            department_stats.append({
                'department': dept.name,
                'present': (
                    dept_non_holiday_logs.filter(first_in_time__isnull=False, is_late=False).count() +
                    dept_holiday_logs.filter(first_in_time__isnull=False).count()
                ),
                'absent': dept_non_holiday_logs.filter(first_in_time__isnull=True).count(),
                'late': dept_non_holiday_logs.filter(is_late=True).count(),
                'leave': Leave.objects.filter(
                    Q(employee__department=dept) &
                    Q(start_date__lte=end_date) & 
                    Q(end_date__gte=start_date) &
                    Q(status='approved')
                ).count()
            })
        return department_stats

    @staticmethod
    def _generate_employee_records(
        base_query: Any,
        holiday_logs: Any,
        non_holiday_logs: Any,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Generate employee records"""
        employee_records = []
        for emp in base_query:
            emp_holiday_logs = holiday_logs.filter(employee=emp)
            emp_non_holiday_logs = non_holiday_logs.filter(employee=emp)
            
            employee_records.append({
                'id': emp.id,
                'name': f"{emp.first_name} {emp.last_name}",
                'department': emp.department.name if emp.department else '-',
                'present_days': (
                    emp_non_holiday_logs.filter(first_in_time__isnull=False, is_late=False).count() +
                    emp_holiday_logs.filter(first_in_time__isnull=False).count()
                ),
                'absent_days': emp_non_holiday_logs.filter(first_in_time__isnull=True).count(),
                'late_days': emp_non_holiday_logs.filter(is_late=True).count(),
                'leave_days': Leave.objects.filter(
                    Q(employee=emp) &
                    Q(start_date__lte=end_date) & 
                    Q(end_date__gte=start_date) &
                    Q(status='approved')
                ).count()
            })
        return employee_records

    @staticmethod
    def _generate_leave_type_stats(leaves: Any) -> List[Dict[str, Any]]:
        """Generate leave type statistics"""
        leave_type_stats = []
        for lt in LeaveType.objects.all():
            lt_leaves = leaves.filter(leave_type=lt)
            if lt_leaves.exists():
                total_days = sum((l.end_date - l.start_date).days + 1 for l in lt_leaves)
                leave_type_stats.append({
                    'leave_type': lt.name,
                    'count': lt_leaves.count(),
                    'avg_duration': total_days / lt_leaves.count() if lt_leaves.count() > 0 else 0
                })
        return leave_type_stats

    @staticmethod
    def _generate_leave_department_stats(leaves: Any) -> List[Dict[str, Any]]:
        """Generate department-wise leave statistics"""
        department_stats = []
        for dept in Department.objects.all():
            dept_leaves = leaves.filter(employee__department=dept)
            if dept_leaves.exists():
                department_stats.append({
                    'department': dept.name,
                    'total_leaves': dept_leaves.count(),
                    'by_type': [
                        {
                            'leave_type': lt.name,
                            'count': dept_leaves.filter(leave_type=lt).count()
                        }
                        for lt in LeaveType.objects.all()
                        if dept_leaves.filter(leave_type=lt).exists()
                    ]
                })
        return department_stats