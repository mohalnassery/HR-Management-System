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
        # Parse ISO format dates with timezone
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date()
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00')).date()

        # Build query
        query = Q(date__range=[start, end])
        if department:
            query &= Q(employee__department_id=department)
        if employee:
            query &= Q(employee_id=employee)

        logs = AttendanceLog.objects.filter(query).select_related('employee')

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
    except (ValueError, TypeError) as e:
        return Response({'error': f'Invalid date format: {str(e)}'}, status=400)


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
