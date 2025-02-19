from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from django.db.models import Q, Count, Avg
from django.core.cache import cache
from django.conf import settings

from attendance.models import AttendanceLog, Leave, Holiday
from employees.models import Employee, Department

class ReportService:
    """Service class for generating various types of attendance and leave reports"""
    
    CACHE_TIMEOUT = 3600  # 1 hour cache timeout
    
    @classmethod
    def get_attendance_report(cls, 
                            start_date: datetime,
                            end_date: datetime,
                            departments: Optional[List[int]] = None,
                            employees: Optional[List[int]] = None,
                            status: Optional[List[str]] = None) -> Dict:
        """
        Generate attendance report for the given parameters
        
        Args:
            start_date: Start date for the report
            end_date: End date for the report
            departments: List of department IDs to filter by
            employees: List of employee IDs to filter by
            status: List of status types to include ('present', 'absent', 'late', 'leave')
            
        Returns:
            Dictionary containing attendance report data
        """
        cache_key = cls._generate_cache_key("attendance", {
            "start_date": start_date,
            "end_date": end_date,
            "departments": departments,
            "employees": employees,
            "status": status
        })
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
            
        # Base query for attendance logs
        query = AttendanceLog.objects.filter(
            date__range=[start_date, end_date]
        )
        
        # Apply filters
        if departments:
            query = query.filter(employee__department_id__in=departments)
        if employees:
            query = query.filter(employee_id__in=employees)
            
        # Calculate statistics
        stats = {
            "present": query.filter(status="present").count(),
            "absent": query.filter(status="absent").count(),
            "late": query.filter(status="late").count(),
            "leave": Leave.objects.filter(
                start_date__lte=end_date,
                end_date__gte=start_date,
                status="approved"
            ).count()
        }
        
        # Get daily trend data
        trend_data = []
        current_date = start_date
        while current_date <= end_date:
            day_stats = {
                "date": current_date.strftime("%Y-%m-%d"),
                "present": query.filter(date=current_date, status="present").count(),
                "absent": query.filter(date=current_date, status="absent").count(),
                "late": query.filter(date=current_date, status="late").count(),
                "leave": Leave.objects.filter(
                    start_date__lte=current_date,
                    end_date__gte=current_date,
                    status="approved"
                ).count()
            }
            trend_data.append(day_stats)
            current_date += timedelta(days=1)
            
        # Get department-wise statistics
        dept_stats = []
        departments_query = Department.objects.all()
        if departments:
            departments_query = departments_query.filter(id__in=departments)
            
        for dept in departments_query:
            dept_query = query.filter(employee__department=dept)
            dept_stats.append({
                "department": dept.name,
                "present": dept_query.filter(status="present").count(),
                "absent": dept_query.filter(status="absent").count(),
                "late": dept_query.filter(status="late").count(),
                "leave": Leave.objects.filter(
                    employee__department=dept,
                    start_date__lte=end_date,
                    end_date__gte=start_date,
                    status="approved"
                ).count()
            })
            
        # Get detailed employee records
        employee_records = []
        employees_query = Employee.objects.filter(
            attendancelog__date__range=[start_date, end_date]
        ).distinct()
        
        if departments:
            employees_query = employees_query.filter(department_id__in=departments)
        if employees:
            employees_query = employees_query.filter(id__in=employees)
            
        for emp in employees_query:
            emp_query = query.filter(employee=emp)
            employee_records.append({
                "id": emp.id,
                "name": f"{emp.first_name} {emp.last_name}",
                "department": emp.department.name,
                "present_days": emp_query.filter(status="present").count(),
                "absent_days": emp_query.filter(status="absent").count(),
                "late_days": emp_query.filter(status="late").count(),
                "leave_days": Leave.objects.filter(
                    employee=emp,
                    start_date__lte=end_date,
                    end_date__gte=start_date,
                    status="approved"
                ).count()
            })
        
        report_data = {
            "summary": stats,
            "trend_data": trend_data,
            "department_stats": dept_stats,
            "employee_records": employee_records
        }
        
        cache.set(cache_key, report_data, cls.CACHE_TIMEOUT)
        return report_data
    
    @classmethod
    def get_leave_report(cls,
                        start_date: datetime,
                        end_date: datetime,
                        departments: Optional[List[int]] = None,
                        employees: Optional[List[int]] = None,
                        leave_types: Optional[List[str]] = None,
                        status: Optional[List[str]] = None) -> Dict:
        """
        Generate leave report for the given parameters
        """
        cache_key = cls._generate_cache_key("leave", {
            "start_date": start_date,
            "end_date": end_date,
            "departments": departments,
            "employees": employees,
            "leave_types": leave_types,
            "status": status
        })
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
            
        # Base query for leaves
        query = Leave.objects.filter(
            Q(start_date__range=[start_date, end_date]) |
            Q(end_date__range=[start_date, end_date])
        )
        
        # Apply filters
        if departments:
            query = query.filter(employee__department_id__in=departments)
        if employees:
            query = query.filter(employee_id__in=employees)
        if leave_types:
            query = query.filter(leave_type__in=leave_types)
        if status:
            query = query.filter(status__in=status)
            
        # Calculate statistics by leave type
        leave_type_stats = query.values('leave_type').annotate(
            count=Count('id'),
            avg_duration=Avg('duration')
        )
        
        # Get department-wise leave statistics
        dept_stats = []
        departments_query = Department.objects.all()
        if departments:
            departments_query = departments_query.filter(id__in=departments)
            
        for dept in departments_query:
            dept_query = query.filter(employee__department=dept)
            dept_stats.append({
                "department": dept.name,
                "total_leaves": dept_query.count(),
                "by_type": dept_query.values('leave_type').annotate(count=Count('id'))
            })
            
        report_data = {
            "leave_type_stats": list(leave_type_stats),
            "department_stats": dept_stats,
            "total_leaves": query.count(),
            "approved_leaves": query.filter(status="approved").count(),
            "pending_leaves": query.filter(status="pending").count(),
            "rejected_leaves": query.filter(status="rejected").count()
        }
        
        cache.set(cache_key, report_data, cls.CACHE_TIMEOUT)
        return report_data
    
    @classmethod
    def get_holiday_report(cls,
                          start_date: datetime,
                          end_date: datetime,
                          departments: Optional[List[int]] = None) -> Dict:
        """
        Generate holiday report for the given parameters
        """
        cache_key = cls._generate_cache_key("holiday", {
            "start_date": start_date,
            "end_date": end_date,
            "departments": departments
        })
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
            
        # Get holidays in date range
        query = Holiday.objects.filter(date__range=[start_date, end_date])
        
        if departments:
            query = query.filter(applicable_departments__in=departments)
            
        holidays = []
        for holiday in query:
            holidays.append({
                "date": holiday.date.strftime("%Y-%m-%d"),
                "name": holiday.name,
                "description": holiday.description,
                "type": holiday.holiday_type
            })
            
        report_data = {
            "total_holidays": len(holidays),
            "holidays": holidays
        }
        
        cache.set(cache_key, report_data, cls.CACHE_TIMEOUT)
        return report_data
    
    @classmethod
    def _generate_cache_key(cls, report_type: str, params: Dict) -> str:
        """Generate a cache key for the given report type and parameters"""
        param_str = "_".join(f"{k}:{v}" for k, v in sorted(params.items()))
        return f"report_{report_type}_{param_str}"