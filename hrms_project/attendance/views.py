from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime, date, timedelta
from employees.models import Employee, Department

from .models import (
    Shift, AttendanceRecord, AttendanceLog,
    AttendanceEdit, Leave, Holiday
)
from .serializers import (
    ShiftSerializer, AttendanceRecordSerializer,
    AttendanceLogSerializer, AttendanceEditSerializer,
    LeaveSerializer, HolidaySerializer
)
from .utils import (
    process_attendance_excel, generate_attendance_log,
    process_daily_attendance, validate_attendance_edit,
    get_attendance_summary
)

# Template Views
@login_required
def attendance_list(request):
    """Display attendance list page"""
    context = {
        'departments': Department.objects.all()
    }
    return render(request, 'attendance/attendance_list.html', context)

@login_required
def calendar_view(request):
    """Display calendar view page"""
    context = {
        'employees': Employee.objects.filter(is_active=True)
    }
    return render(request, 'attendance/calendar.html', context)

@login_required
def mark_attendance(request):
    """Display manual attendance marking page"""
    context = {
        'employees': Employee.objects.filter(is_active=True),
        'shifts': Shift.objects.filter(is_active=True)
    }
    return render(request, 'attendance/mark_attendance.html', context)

@login_required
def leave_request_list(request):
    """Display leave requests list page"""
    return render(request, 'attendance/leave_request_list.html')

@login_required
def leave_request_create(request):
    """Display leave request creation page"""
    return render(request, 'attendance/leave_request_form.html')

@login_required
def leave_request_detail(request, pk):
    """Display leave request details page"""
    leave = get_object_or_404(Leave, pk=pk)
    return render(request, 'attendance/leave_request_detail.html', {'leave': leave})

@login_required
def upload_attendance(request):
    """Display attendance upload page"""
    return render(request, 'attendance/upload_attendance.html')

# API ViewSets
class ShiftViewSet(viewsets.ModelViewSet):
    """ViewSet for managing shifts"""
    serializer_class = ShiftSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Shift.objects.filter(is_active=True)

class AttendanceRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for managing raw attendance records"""
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated]
    queryset = AttendanceRecord.objects.all()

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def upload_excel(self, request):
        """Handle Excel file upload"""
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            excel_file = request.FILES['file']
            records_created, duplicates, total_records = process_attendance_excel(excel_file)
            logs_created = process_daily_attendance()

            return Response({
                'message': 'File processed successfully',
                'new_records': records_created,
                'duplicate_records': duplicates,
                'total_records': total_records,
                'logs_created': logs_created,
                'success': True
            })
        except Exception as e:
            return Response({
                'error': str(e),
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)

class AttendanceLogViewSet(viewsets.ModelViewSet):
    """ViewSet for managing processed attendance logs"""
    serializer_class = AttendanceLogSerializer
    permission_classes = [IsAuthenticated]
    queryset = AttendanceLog.objects.all()

    def get_queryset(self):
        queryset = AttendanceLog.objects.filter(is_active=True)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        employee_id = self.request.query_params.get('employee')
        department_id = self.request.query_params.get('department')

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)

        return queryset

class LeaveViewSet(viewsets.ModelViewSet):
    """ViewSet for managing leave requests"""
    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]
    queryset = Leave.objects.all()

    def get_queryset(self):
        queryset = Leave.objects.filter(is_active=True)
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

class HolidayViewSet(viewsets.ModelViewSet):
    """ViewSet for managing holidays"""
    serializer_class = HolidaySerializer
    permission_classes = [IsAuthenticated]
    queryset = Holiday.objects.all()

    def get_queryset(self):
        return Holiday.objects.filter(is_active=True)

# API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_calendar_events(request):
    """Get events for calendar view"""
    start_date = request.query_params.get('start')
    end_date = request.query_params.get('end')
    employee_id = request.query_params.get('employee')

    events = []

    # Get attendance logs
    logs = AttendanceLog.objects.filter(
        date__range=[start_date, end_date],
        is_active=True
    )
    if employee_id:
        logs = logs.filter(employee_id=employee_id)

    for log in logs:
        events.append({
            'id': log.id,
            'title': f"{log.employee.get_full_name()} ({log.get_status_display()})",
            'date': log.date,
            'status': log.status,
            'employee_name': log.employee.get_full_name()
        })

    # Add holidays
    holidays = Holiday.objects.filter(
        date__range=[start_date, end_date],
        is_active=True
    )
    for holiday in holidays:
        events.append({
            'title': holiday.description,
            'date': holiday.date,
            'status': 'holiday'
        })

    return Response(events)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_employee_attendance(request, employee_id):
    """Get attendance summary for an employee"""
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if not start_date or not end_date:
        return Response(
            {'error': 'Start date and end date are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        employee = get_object_or_404(Employee, id=employee_id)
        summary = get_attendance_summary(employee, start_date, end_date)
        return Response(summary)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
