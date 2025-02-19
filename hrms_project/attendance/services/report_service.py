from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from django.db.models import Count, Q
from django.core.cache import cache
from django.utils import timezone

from ..models import (
    AttendanceLog, Leave, Holiday, LeaveType
)
from employees.models import Employee, Department

class ReportService:
    """Service class for generating various attendance reports"""
    
    CACHE_TIMEOUT = 3600  # 1 hour cache timeout
    
    @classmethod
    def _get_cache_key(cls, report_type: str, **params) -> str:
        """Generate a cache key based on report type and parameters"""
        param_str = "_".join(f"{k}:{v}" for k, v in sorted(params.items()))
        return f"report_{report_type}_{param_str}"
    
    @classmethod
    def get_attendance_report(cls, start_date: datetime, end_date: datetime,
                            departments: List[int] = None,
                            employees: List[int] = None,
                            status: List[str] = None) -> Dict[str, Any]:
        """
        Generate attendance report for the given parameters
        """
        # Check cache first
        cache_key = cls._get_cache_key(
            'attendance',
            departments=departments,
            employees=employees,
            end_date=end_date,
            start_date=start_date,
            status=status
        )
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
            
        # Build base query for employees
        base_query = Employee.objects.all()
        
        # Apply filters
        if departments:
            base_query = base_query.filter(department_id__in=departments)
        if employees:
            base_query = base_query.filter(id__in=employees)
            
        # Get attendance records for the date range
        attendance_logs = AttendanceLog.objects.filter(
            date__range=[start_date, end_date]
        )
        
        # Calculate summary statistics
        present_count = attendance_logs.filter(
            first_in_time__isnull=False,
            is_late=False
        ).count()
        
        late_count = attendance_logs.filter(is_late=True).count()
        absent_count = attendance_logs.filter(first_in_time__isnull=True).count()
        
        leave_count = Leave.objects.filter(
            Q(start_date__lte=end_date) & 
            Q(end_date__gte=start_date) &
            Q(status='approved')
        ).count()
        
        # Get daily trend data
        trend_data = []
        current_date = start_date
        while current_date <= end_date:
            day_logs = attendance_logs.filter(date=current_date)
            trend_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'present': day_logs.filter(first_in_time__isnull=False, is_late=False).count(),
                'absent': day_logs.filter(first_in_time__isnull=True).count(),
                'late': day_logs.filter(is_late=True).count(),
                'leave': Leave.objects.filter(
                    Q(start_date__lte=current_date) & 
                    Q(end_date__gte=current_date) &
                    Q(status='approved')
                ).count()
            })
            current_date += timedelta(days=1)
            
        # Get department statistics
        department_stats = []
        for dept in Department.objects.all():
            dept_logs = attendance_logs.filter(employee__department=dept)
            department_stats.append({
                'department': dept.name,
                'present': dept_logs.filter(first_in_time__isnull=False, is_late=False).count(),
                'absent': dept_logs.filter(first_in_time__isnull=True).count(),
                'late': dept_logs.filter(is_late=True).count(),
                'leave': Leave.objects.filter(
                    Q(employee__department=dept) &
                    Q(start_date__lte=end_date) & 
                    Q(end_date__gte=start_date) &
                    Q(status='approved')
                ).count()
            })
            
        # Get employee records
        employee_records = []
        for emp in base_query:
            emp_logs = attendance_logs.filter(employee=emp)
            employee_records.append({
                'id': emp.id,
                'name': f"{emp.first_name} {emp.last_name}",
                'department': emp.department.name if emp.department else '-',
                'present_days': emp_logs.filter(first_in_time__isnull=False, is_late=False).count(),
                'absent_days': emp_logs.filter(first_in_time__isnull=True).count(),
                'late_days': emp_logs.filter(is_late=True).count(),
                'leave_days': Leave.objects.filter(
                    Q(employee=emp) &
                    Q(start_date__lte=end_date) & 
                    Q(end_date__gte=start_date) &
                    Q(status='approved')
                ).count()
            })
            
        # Prepare report data
        report_data = {
            'summary': {
                'present': present_count,
                'absent': absent_count,
                'late': late_count,
                'leave': leave_count
            },
            'trend_data': trend_data,
            'department_stats': department_stats,
            'employee_records': employee_records,
            'start_date': start_date,
            'end_date': end_date,
            'generated_at': timezone.now()
        }
        
        # Cache the report
        cache.set(cache_key, report_data, cls.CACHE_TIMEOUT)
        
        return report_data
    
    @classmethod
    def get_leave_report(cls, start_date: datetime, end_date: datetime,
                        departments: List[int] = None,
                        employees: List[int] = None,
                        leave_types: List[str] = None) -> Dict[str, Any]:
        """
        Generate leave report for the given parameters
        """
        # Check cache first
        cache_key = cls._get_cache_key(
            'leave',
            departments=departments,
            employees=employees,
            end_date=end_date,
            start_date=start_date,
            leave_types=leave_types
        )
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
            
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
        
        # Get leave type statistics
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
        
        # Get department statistics
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
        
        # Get employee records
        employee_records = []
        for leave in leaves:
            employee_records.append({
                'employee_name': f"{leave.employee.first_name} {leave.employee.last_name}",
                'department': leave.employee.department.name if leave.employee.department else '-',
                'leave_type': leave.leave_type.name,
                'start_date': leave.start_date,
                'end_date': leave.end_date,
                'duration': (leave.end_date - leave.start_date).days + 1,
                'status': leave.status
            })
        
        report_data = {
            'total_leaves': total_leaves,
            'approved_leaves': approved_leaves,
            'pending_leaves': pending_leaves,
            'rejected_leaves': rejected_leaves,
            'leave_type_stats': leave_type_stats,
            'department_stats': department_stats,
            'employee_records': employee_records,
            'start_date': start_date,
            'end_date': end_date,
            'generated_at': timezone.now()
        }
        
        # Cache the report
        cache.set(cache_key, report_data, cls.CACHE_TIMEOUT)
        
        return report_data
    
    @classmethod
    def get_holiday_report(cls, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Generate holiday report for the given date range
        """
        # Check cache first
        cache_key = cls._get_cache_key(
            'holiday',
            start_date=start_date,
            end_date=end_date
        )
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
            
        # Get holidays
        holidays = Holiday.objects.filter(
            date__range=[start_date, end_date],
            is_active=True
        ).order_by('date')
        
        # Calculate statistics
        holiday_type_stats = []
        holiday_types = holidays.values('type').annotate(count=Count('type'))
        for ht in holiday_types:
            holiday_type_stats.append({
                'type': ht['type'],
                'count': ht['count']
            })
            
        # Monthly distribution
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
            
        monthly_distribution = list(months.values())
        
        report_data = {
            'total_holidays': holidays.count(),
            'holidays': [
                {
                    'date': h.date,
                    'name': h.name,
                    'type': h.type,
                    'description': h.description
                }
                for h in holidays
            ],
            'holiday_type_stats': holiday_type_stats,
            'monthly_distribution': monthly_distribution,
            'start_date': start_date,
            'end_date': end_date,
            'generated_at': timezone.now()
        }
        
        # Cache the report
        cache.set(cache_key, report_data, cls.CACHE_TIMEOUT)
        
        return report_data