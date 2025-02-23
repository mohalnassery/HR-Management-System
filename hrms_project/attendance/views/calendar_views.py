from datetime import datetime
from django.db.models import Q

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from employees.models import Employee, Department
from attendance.models import (
    AttendanceRecord, AttendanceLog, Leave, Holiday, LeaveType,
    RamadanPeriod
)
from attendance.services import ShiftService, RamadanService


@login_required
def calendar_view(request):
    """View for displaying attendance calendar"""
    return render(request, 'attendance/calendar.html')

@login_required
def calendar_month(request):
    """View for monthly calendar"""
    context = {
        'view_type': 'month',
        'departments': Department.objects.all()
    }
    return render(request, 'attendance/calendar.html', context)

@login_required
def calendar_week(request):
    """View for weekly calendar"""
    context = {
        'view_type': 'week',
        'departments': Department.objects.all()
    }
    return render(request, 'attendance/calendar.html', context)

@login_required
def calendar_department(request):
    """View for department-wise calendar"""
    context = {
        'view_type': 'department',
        'departments': Department.objects.all()
    }
    return render(request, 'attendance/calendar.html', context)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calendar_events(request):
    """Get attendance events for calendar"""
    start_date = request.query_params.get('start')
    end_date = request.query_params.get('end')
    department = request.query_params.get('department')
    employee = request.query_params.get('employee')

    try:
        # Parse dates in YYYY-MM-DD format
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Get holidays in the date range
        holidays = Holiday.objects.filter(
            date__range=[start, end],
            is_active=True
        )
        
        # Create holiday events first
        events = []
        for holiday in holidays:
            events.append({
                'id': f'holiday_{holiday.id}',
                'title': holiday.name,  # Show holiday name instead of employee
                'start': holiday.date.isoformat(),
                'end': holiday.date.isoformat(),
                'color': '#6f42c1',  # purple for holidays
                'allDay': True,
                'extendedProps': {
                    'type': 'holiday',
                    'holiday_type': holiday.holiday_type,
                    'description': holiday.description,
                    'tooltip': f"{holiday.name} - {holiday.description if holiday.description else ''}"
                }
            })

        # Build query for attendance logs
        query = Q(date__range=[start, end])
        if department:
            query &= Q(employee__department_id=department)
        if employee:
            query &= Q(employee_id=employee)

        logs = AttendanceLog.objects.filter(query).select_related('employee')

        def calculate_late_by(log):
            if not log.first_in_time or not log.shift:
                return None
            shift_start = log.shift.start_time
            first_in = log.first_in_time
            if first_in > shift_start:
                late_by = datetime.combine(log.date, first_in) - datetime.combine(log.date, shift_start)
                return str(late_by)
            return None

        def calculate_work_hours(log):
            if not log.first_in_time or not log.last_out_time:
                return None
            work_time = datetime.combine(log.date, log.last_out_time) - datetime.combine(log.date, log.first_in_time)
            return str(work_time)

        attendance_events = []
        for log in logs:
            # Skip weekends (Friday) unless there's attendance
            if log.date.weekday() == 4:  # Friday is 4 in Python's weekday() (0 = Monday)
                if not log.first_in_time:
                    continue  # Skip showing absent on Fridays
            
            status = log.status.title()
            
            # Set color based on status
            if status == 'Present':
                color = '#28a745'  # green
            elif status == 'Absent' and log.date.weekday() != 4:  # Don't show absent for Fridays
                color = '#dc3545'  # red
            elif status == 'Late':
                color = '#ffc107'  # yellow
            elif status == 'Leave':
                color = '#17a2b8'  # cyan
            else:
                continue  # Skip other statuses like holiday since we handle them separately

            event = {
                'id': f'attendance_{log.id}',
                'title': f"{log.employee.get_full_name()} - {status}",
                'start': log.date.isoformat(),
                'end': log.date.isoformat(),
                'color': color,
                'extendedProps': {
                    'type': 'attendance',
                    'employee_id': log.employee.id,
                    'employee': log.employee.get_full_name(),
                    'department': log.employee.department.name if log.employee.department else None,
                    'status': status,
                    'status_color': color.replace('#', ''),
                    'time_in': log.first_in_time.strftime('%I:%M %p') if log.first_in_time else None,
                    'time_out': log.last_out_time.strftime('%I:%M %p') if log.last_out_time else None,
                    'late_by': calculate_late_by(log),
                    'work_hours': calculate_work_hours(log),
                    'tooltip': f"{log.employee.get_full_name()} - {status}\n" +
                             f"In: {log.first_in_time.strftime('%I:%M %p') if log.first_in_time else 'N/A'}\n" +
                             f"Out: {log.last_out_time.strftime('%I:%M %p') if log.last_out_time else 'N/A'}"
                }
            }
            attendance_events.append(event)

        events.extend(attendance_events)

        return Response(events)
    except (ValueError, TypeError) as e:
        print(e)
        return Response({
            'error': f'Invalid date format. Expected YYYY-MM-DD, received: start={start_date}, end={end_date}',
            'details': str(e)
        }, status=400)


# API Views - Keep these API views here as they are general API related
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_calendar_events(request):
    """API endpoint for getting calendar events"""
    start_date = request.query_params.get('start')
    end_date = request.query_params.get('end')
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        logs = AttendanceLog.objects.filter(
            date__range=[start, end]
        ).select_related('employee')
        
        events = []
        for log in logs:
            status = 'Present'
            color = '#28a745'  # green
            
            if not log.first_in_time:
                status = 'Absent'
                color = '#dc3545'  # red
            elif log.is_late:
                status = 'Late'
                color = '#ffc107'  # yellow
                
            events.append({
                'id': log.id,
                'title': f"{log.employee.get_full_name()} - {status}",
                'start': log.date.isoformat(),
                'end': log.date.isoformat(),
                'color': color,
                'extendedProps': {
                    'employee_id': log.employee.id,
                    'status': status,
                    'in_time': log.first_in_time.strftime('%H:%M') if log.first_in_time else None,
                    'out_time': log.last_out_time.strftime('%H:%M') if log.last_out_time else None
                }
            })
            
        return Response(events)
    except (ValueError, TypeError):
        return Response({'error': 'Invalid date format'}, status=400)
