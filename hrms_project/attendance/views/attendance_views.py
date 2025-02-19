from datetime import datetime, date, timedelta, time
from typing import List, Dict, Any

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from django.core.management import call_command
from django.core.paginator import Paginator
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.pagination import PageNumberPagination

from employees.models import Employee, Department
from attendance.models import (
    AttendanceRecord, AttendanceLog, Leave, Holiday, LeaveType,
    RamadanPeriod, ShiftAssignment
)
from attendance.services import ShiftService, RamadanService
from attendance.services.report_service import ReportService
from attendance.serializers import (
    ShiftSerializer, AttendanceRecordSerializer, AttendanceLogSerializer,
    LeaveSerializer, HolidaySerializer
)
from attendance.utils import process_attendance_excel, process_daily_attendance, get_attendance_summary

@login_required
def attendance_list(request):
    """Display attendance list page"""
    # Get filter parameters
    start_date = request.GET.get('start_date', date.today().strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', date.today().strftime('%Y-%m-%d'))
    department = request.GET.get('department', '')
    search = request.GET.get('search', '')

    # Base queryset
    queryset = AttendanceLog.objects.filter(date=date.today())

    # Apply filters
    if department:
        queryset = queryset.filter(employee__department_id=department)
    if search:
        queryset = queryset.filter(
            Q(employee__first_name__icontains=search) |
            Q(employee__last_name__icontains=search) |
            Q(employee__employee_number__icontains=search)
        )

    # Get holidays for the current date
    is_holiday = Holiday.objects.filter(
        Q(date=date.today()) & Q(is_active=True)
    ).exists()

    # Calculate summary counts
    if is_holiday:
        # On holidays, only count people who came to work
        present_count = queryset.filter(first_in_time__isnull=False).count()
        late_count = 0
        absent_count = 0
        # Filter out absent employees on holidays
        queryset = queryset.filter(first_in_time__isnull=False)
    else:
        present_count = queryset.filter(first_in_time__isnull=False, is_late=False).count()
        late_count = queryset.filter(is_late=True).count()
        absent_count = queryset.filter(first_in_time__isnull=True).count()

    on_leave_count = Leave.objects.filter(
        Q(start_date__lte=date.today()) &
        Q(end_date__gte=date.today()) &
        Q(status='approved')
    ).count()

    context = {
        'departments': Department.objects.all(),
        'present_count': present_count,
        'late_count': late_count,
        'absent_count': absent_count,
        'on_leave_count': on_leave_count,
    }
    return render(request, 'attendance/attendance_list.html', context)

@login_required
def mark_attendance(request):
    """View for manual attendance marking"""
    return render(request, 'attendance/mark_attendance.html')

@login_required
def upload_attendance(request):
    """Display attendance upload page"""
    return render(request, 'attendance/upload_attendance.html')

@login_required
def attendance_report(request):
    """
    View for the attendance report page.
    Initializes the page with departments and other necessary data.
    The actual report data is loaded via AJAX using the API endpoints.
    """
    context = {
        'departments': Department.objects.all(),
        'today': date.today().strftime('%Y-%m-%d'),
        'title': 'Attendance Reports',  # For page title
        'active_tab': 'reports'  # For navigation highlighting
    }

    return render(request, 'attendance/attendance_report.html', context)

@login_required
def attendance_detail_view(request):
    """View for displaying and editing attendance details"""
    try:
        personnel_id = request.GET.get('personnel_id')
        employee_id = request.GET.get('employee_id')  # Support both ID types
        date_str = request.GET.get('date')

        # Get employee by either personnel_id or employee_id
        if personnel_id:
            employee = get_object_or_404(Employee, employee_number=personnel_id)
        elif employee_id:
            employee = get_object_or_404(Employee, id=employee_id)
        else:
            raise Http404("Missing employee identifier")

        # Handle date parameter
        if date_str:
            try:
                # Try parsing YYYY-MM-DD format first
                date_obj = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
            except ValueError:
                try:
                    # Fallback to MMM DD, YYYY format
                    date_obj = datetime.strptime(date_str.strip(), '%b %d, %Y').date()
                except ValueError:
                    raise Http404("Invalid date format")

            log = get_object_or_404(AttendanceLog, employee=employee, date=date_obj)

            # Get all raw attendance records for this date
            records = AttendanceRecord.objects.filter(
                employee=employee,
                timestamp__date=date_obj,
                is_active=True
            ).order_by('timestamp')

            context = get_attendance_detail_context(employee, log, records)

        else:
            # If no date specified, show monthly view
            start_date = request.GET.get('start_date', date.today().replace(day=1).strftime('%Y-%m-%d'))
            end_date = request.GET.get('end_date', date.today().strftime('%Y-%m-%d'))

            attendance_logs = AttendanceLog.objects.filter(
                employee=employee,
                date__range=[start_date, end_date]
            ).order_by('-date')

            # Paginate results
            paginator = Paginator(attendance_logs, 31)  # Show up to a month of records per page
            page = request.GET.get('page', 1)
            attendance_records = paginator.get_page(page)

            context = {
                'employee': employee,
                'attendance_records': attendance_records,
                'start_date': start_date,
                'end_date': end_date,
                'title': f'Attendance Detail - {employee.first_name} {employee.last_name}',
                'active_tab': 'reports'
            }

        return render(request, 'attendance/attendance_detail.html', context)

    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=500)
        messages.error(request, f"Error loading attendance details: {str(e)}")
        return redirect('attendance:attendance_list')

@login_required
def reprocess_attendance_view(request):
    """View for triggering attendance reprocessing"""
    if request.method == 'POST':
        try:
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            employee_id = request.POST.get('employee_id')

            command_args = []

            if start_date and end_date:
                command_args.extend(['--date-range', start_date, end_date])
            elif start_date:
                command_args.extend(['--date', start_date])

            if employee_id:
                command_args.extend(['--employee-id', employee_id])

            # Call the management command
            call_command('reprocess_attendance', *command_args)

            messages.success(request, "Attendance logs have been reprocessed successfully")
        except Exception as e:
            messages.error(request, f"Error reprocessing attendance logs: {str(e)}")

    return redirect('attendance:attendance_list')

def get_attendance_detail_context(employee, log, records):
    """Helper function to get context for attendance detail view"""
    # Find first IN and last OUT records
    first_in_record = None
    last_out_record = None
    for record in records:
        if record.event_point == 'IN':
            if not first_in_record:
                first_in_record = record
        elif record.event_point == 'OUT':
            last_out_record = record

    raw_records = []
    for record in records:
        is_first_in = record == first_in_record
        is_last_out = record == last_out_record

        raw_records.append({
            'id': record.id,
            'time': record.timestamp.strftime('%I:%M %p'),
            'event_point': record.event_point,
            'description': record.event_description or 'Normal Punch',
            'device': record.device_name or 'Unknown Device',
            'is_first_in': is_first_in,
            'is_last_out': is_last_out,
            'label': ' (First)' if is_first_in else (' (Last)' if is_last_out else ''),
            'row_class': 'table-primary' if is_first_in or is_last_out else ''
        })

    # Calculate total hours
    total_hours = 0
    if log.first_in_time and log.last_out_time:
        first_in = datetime.combine(log.date, log.first_in_time)
        last_out = datetime.combine(log.date, log.last_out_time)
        duration = last_out - first_in
        total_hours = round(duration.total_seconds() / 3600, 2)

    return {
        'employee_name': employee.get_full_name(),
        'personnel_id': employee.employee_number,
        'department': employee.department.name if employee.department else '-',
        'designation': employee.designation or '-',
        'date': log.date.strftime('%b %d, %Y'),
        'day': log.date.strftime('%A'),
        'raw_records': raw_records,
        'stats': {
            'status': 'Late' if log.is_late else ('Present' if log.first_in_time else 'Absent'),
            'total_hours': f"{total_hours:.2f}",
            'first_in': log.first_in_time.strftime('%I:%M %p') if log.first_in_time else '-',
            'last_out': log.last_out_time.strftime('%I:%M %p') if log.last_out_time else '-',
            'is_late': log.is_late
        }
    }

@login_required
def attendance_report(request):
    """View for displaying attendance reports and analytics"""
    context = {
        'departments': Department.objects.all()
    }
    return render(request, 'attendance/attendance_report.html', context)

@login_required
def reprocess_attendance_view(request):
    """View for triggering attendance reprocessing"""
    if request.method == 'POST':
        try:
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            employee_id = request.POST.get('employee_id')

            command_args = []
            
            if start_date and end_date:
                command_args.extend(['--date-range', start_date, end_date])
            elif start_date:
                command_args.extend(['--date', start_date])
                
            if employee_id:
                command_args.extend(['--employee-id', employee_id])

            # Call the management command
            call_command('reprocess_attendance', *command_args)
            
            messages.success(request, "Attendance logs have been reprocessed successfully")
        except Exception as e:
            messages.error(request, f"Error reprocessing attendance logs: {str(e)}")

    return redirect('attendance:attendance_list')

# API ViewSets
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
            records_created, duplicates, total_records, new_employees, unique_dates = process_attendance_excel(excel_file)

            # Process logs for each unique date in the uploaded file
            logs_created = 0
            for date_obj in unique_dates:
                logs_created += process_daily_attendance(date_obj)

            return Response({
                'message': 'File processed successfully',
                'new_records': records_created,
                'duplicate_records': duplicates,
                'total_records': total_records,
                'logs_created': logs_created,
                'new_employees': new_employees,
                'success': True
            })
        except Exception as e:
            return Response({
                'error': str(e),
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)

class LargeResultsSetPagination(PageNumberPagination):
    """Custom pagination class for large result sets"""
    page_size = 400
    page_size_query_param = 'page_size'
    max_page_size = 1000

class AttendanceLogViewSet(viewsets.ModelViewSet):
    """ViewSet for managing processed attendance logs"""
    serializer_class = AttendanceLogSerializer
    permission_classes = [IsAuthenticated]
    queryset = AttendanceLog.objects.all()
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        queryset = AttendanceLog.objects.select_related('employee').all()
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

# API Views

class LargeResultsSetPagination(PageNumberPagination):
    """Custom pagination class for large result sets"""
    page_size = 400
    page_size_query_param = 'page_size'
    max_page_size = 1000

class AttendanceLogListViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for listing and retrieving attendance logs with filtering"""
    serializer_class = AttendanceLogSerializer
    permission_classes = [IsAuthenticated]
    queryset = AttendanceLog.objects.select_related('employee').all()
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-date')

        # Get filter parameters
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        department = self.request.query_params.get('department')
        status = self.request.query_params.get('status')
        search = self.request.query_params.get('search')

        # Apply filters
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=start_date)
            except ValueError:
                pass

        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=end_date)
            except ValueError:
                pass

        if department:
            queryset = queryset.filter(employee__department_id=department)

        if status:
            if status == 'late':
                queryset = queryset.filter(is_late=True)
            elif status == 'present':
                queryset = queryset.filter(first_in_time__isnull=False)
            elif status == 'absent':
                queryset = queryset.filter(first_in_time__isnull=True)

        if search:
            queryset = queryset.filter(
                Q(employee__first_name__icontains=search) |
                Q(employee__last_name__icontains=search) |
                Q(employee__employee_number__icontains=search)
            )

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Get date parameters and parse them
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        try:
            if not start_date:
                start_date = date.today()
            else:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                
            if not end_date:
                end_date = date.today()
            else:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = date.today()
            end_date = date.today()

        # Check for holidays in the date range
        holidays_in_range = Holiday.objects.filter(
            Q(date__range=[start_date, end_date]) & Q(is_active=True)
        )
        holiday_dates = set(h.date for h in holidays_in_range)

        # For holiday dates, only include employees who came to work
        holiday_queryset = queryset.filter(date__in=holiday_dates, first_in_time__isnull=False)
        non_holiday_queryset = queryset.exclude(date__in=holiday_dates)

        # Combine querysets
        queryset = non_holiday_queryset | holiday_queryset

        # Calculate summary counts
        present_count = (
            non_holiday_queryset.filter(first_in_time__isnull=False, is_late=False).count() +
            holiday_queryset.filter(first_in_time__isnull=False).count()
        )
        late_count = non_holiday_queryset.filter(is_late=True).count()
        absent_count = non_holiday_queryset.filter(first_in_time__isnull=True).count()
        
        # Get on leave count with proper date validation
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        # Use today's date if no valid dates are provided
        try:
            if not start_date:
                start_date = date.today()
            else:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                
            if not end_date:
                end_date = date.today()
            else:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            # If date parsing fails, default to today
            start_date = date.today()
            end_date = date.today()

        on_leave_count = Leave.objects.filter(
            Q(start_date__lte=end_date) & 
            Q(end_date__gte=start_date) &
            Q(status='approved')
        ).count()

        # Get paginated results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['summary'] = {
                'present': present_count,
                'absent': absent_count,
                'late': late_count,
                'leave': on_leave_count
            }
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'summary': {
                'present': present_count,
                'absent': absent_count,
                'late': late_count,
                'leave': on_leave_count
            }
        })

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


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

@api_view(['GET'])
def attendance_details(request):
    """Get detailed attendance information for a specific log"""
    try:
        personnel_id = request.GET.get('personnel_id')
        date_str = request.GET.get('date')

        if not personnel_id or not date_str:
            return Response({'error': 'Missing required parameters'}, status=400)

        try:
            # Try parsing YYYY-MM-DD format
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                # Fallback to MMM DD, YYYY format
                date = datetime.strptime(date_str, '%b %d, %Y').date()
            except ValueError:
                return Response({'error': 'Invalid date format. Expected YYYY-MM-DD or MMM DD, YYYY'}, status=400)

        employee = Employee.objects.get(employee_number=personnel_id)
        log = AttendanceLog.objects.select_related('employee').get(employee=employee, date=date)

        # Get raw attendance records for this date
        records = AttendanceRecord.objects.filter(
            employee=employee,
            timestamp__date=date,
            is_active=True
        ).order_by('timestamp')

        raw_records = []
        for record in records:
            raw_records.append({
                'id': record.id,
                'time': record.timestamp.strftime('%I:%M %p'),
                'device': record.device_name or 'Unknown Device',
                'event_point': record.event_point,
                'description': record.event_description or 'Normal Punch'
            })

        # Calculate total hours
        total_hours = 0
        if log.first_in_time and log.last_out_time:
            first_in = datetime.combine(date, log.first_in_time)
            last_out = datetime.combine(date, log.last_out_time)
            duration = last_out - first_in
            total_hours = round(duration.total_seconds() / 3600, 2)

        return Response({
            'log_id': log.id,
            'date': log.date.strftime('%b %d, %Y'),
            'employee': log.employee.get_full_name(),
            'status': 'Late' if log.is_late else ('Present' if log.first_in_time else 'Absent'),
            'source': log.source or '-',
            'stats': {
                'status': 'Late' if log.is_late else ('Present' if log.first_in_time else 'Absent'),
                'total_hours': f"{total_hours:.2f}",
                'first_in': log.first_in_time.strftime('%I:%M %p') if log.first_in_time else '-',
                'last_out': log.last_out_time.strftime('%I:%M %p') if log.last_out_time else '-',
                'is_late': log.is_late
            },
            'raw_records': raw_records
        })
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@api_view(['GET'])
def get_department_employees(request):
    """AJAX view to get employees by department"""
    department_id = request.GET.get('department')
    search_query = request.GET.get('q', '').strip()

    if search_query:
        employees = Employee.objects.filter(
            Q(employee_number__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
        if department_id:
            employees = employees.filter(department_id=department_id)
    elif department_id:
        employees = Employee.objects.filter(department_id=department_id)
    else:
        employees = Employee.objects.all()

    employees = employees.values('id', 'user__first_name', 'user__last_name')

    employee_list = [
        {
            'id': emp['id'],
            'name': f"{emp['user__first_name']} {emp['user__last_name']}"
        }
        for emp in employees
    ]

    return JsonResponse({'employees': employee_list})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attendance_detail_api(request):
    """API endpoint for getting attendance details"""
    try:
        personnel_id = request.GET.get('personnel_id')
        date_str = request.GET.get('date')

        if not personnel_id or not date_str:
            return Response({'error': 'Missing required parameters'}, status=400)

        try:
            date_obj = datetime.strptime(date_str.strip(), '%b %d, %Y').date()
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=400)

        employee = Employee.objects.get(employee_number=personnel_id)
        log = AttendanceLog.objects.select_related('employee').get(employee=employee, date=date_obj)
        data = {
            'id': log.id,
            'employee_name': log.employee.get_full_name(),
            'personnel_id': log.employee.employee_number,
            'department': log.employee.department.name if log.employee.department else None,
            'designation': log.employee.designation,
            'date': log.date,
            'records': [
                {
                    'id': log.id,
                    'timestamp': log.first_in_time.isoformat() if log.first_in_time else None,
                    'event_point': 'IN',
                    'source': log.source,
                    'device_name': log.device
                }
            ]
        }

        # Add out time if exists
        if log.last_out_time:
            data['records'].append({
                'id': log.id,
                'timestamp': log.last_out_time.isoformat(),
                'event_point': 'OUT',
                'source': log.source,
                'device_name': log.device
            })

        return Response(data)
    except AttendanceLog.DoesNotExist:
        return Response({'error': 'Log not found'}, status=404)

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def attendance_record_api(request, record_id):
    """API endpoint for updating or deleting attendance records"""
    try:
        log = AttendanceLog.objects.get(id=record_id)

        if request.method == 'DELETE':
            log.delete()
            return Response(status=204)

        if request.method == 'PATCH':
            time_str = request.data.get('time')
            reason = request.data.get('reason')

            if not time_str or not reason:
                return Response({'error': 'Time and reason are required'}, status=400)

            # Parse the time string
            try:
                hour, minute = map(int, time_str.split(':'))
                new_time = datetime.combine(log.date, time(hour, minute))

                # Update the appropriate time field based on the record type - assuming first record is IN and last is OUT
                records = AttendanceRecord.objects.filter(
                    attendancelog=log
                ).order_by('timestamp')

                if records.exists():
                    first_record = records.first()
                    last_record = records.last()

                    if log.first_in_time and log.first_in_time == first_record.timestamp.time(): #compare time not datetime
                        log.first_in_time = new_time.time() # set time only
                    elif log.last_out_time and log.last_out_time == last_record.timestamp.time(): #compare time not datetime
                        log.last_out_time = new_time.time() # set time only

                log.save()
                return Response({'status': 'success'})
            except ValueError:
                return Response({'error': 'Invalid time format'}, status=400)

    except AttendanceLog.DoesNotExist:
        return Response({'error': 'Record not found'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_attendance_record(request):
    """API endpoint for adding a new attendance record"""
    personnel_id = request.data.get('personnel_id')
    date_str = request.data.get('date')
    time_str = request.data.get('time')
    event_point = request.data.get('type') # using event_point instead of type as in models
    device_name = request.data.get('device_name') # device name
    reason = request.data.get('reason') # remarks instead of reason to match model field

    if not all([personnel_id, date_str, time_str, event_point, reason, device_name]): #check device_name and reason
        return Response({'error': 'All fields are required'}, status=400)

    try:
        employee = Employee.objects.get(employee_number=personnel_id)
        log_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        record_time = datetime.strptime(time_str, '%H:%M').time() # only time part

        timestamp = datetime.combine(log_date, record_time) # combine date and time for timestamp

        # Create attendance record
        record = AttendanceRecord.objects.create(
            employee=employee,
            timestamp=timestamp,
            event_point=event_point, # use event_point
            device_name=device_name, # use device_name
            remarks=reason, # use remarks for reason
            source='manual' # set source to manual
        )

        return Response({'status': 'success', 'record_id': record.id }, status=status.HTTP_201_CREATED)

    except Employee.DoesNotExist:
        return Response({'error': 'Employee not found'}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError as e:
        return Response({'error': f'Invalid data: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': f'Error creating record: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def search_employees(request):
    """Search employees by ID or name"""
    query = request.GET.get('q', '').strip()
    department_id = request.GET.get('department')

    if not query:
        return Response([])

    try:
        # Build the query
        employee_query = Q(employee_number__icontains=query) | \
                        Q(first_name__icontains=query) | \
                        Q(last_name__icontains=query)

        # Add department filter if specified
        if department_id:
            employee_query &= Q(department_id=department_id)

        # Get employees matching the criteria
        employees = Employee.objects.filter(employee_query, is_active=True) \
                                 .select_related('department') \
                                 .order_by('employee_number')[:10]

        # Format response
        employee_list = [{
            'id': emp.id,
            'employee_number': emp.employee_number,
            'full_name': emp.get_full_name(),
            'department': emp.department.name if emp.department else None
        } for emp in employees]

        return Response(employee_list)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )