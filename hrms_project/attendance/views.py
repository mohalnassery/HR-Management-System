from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from django.http import JsonResponse, Http404
from django.db.models import Q
from datetime import datetime, date, timedelta, time
from employees.models import Employee, Department
from time import time as time_func
from django.utils.dateparse import parse_datetime
from django.contrib import messages
from django.utils import timezone
from django.db import models

from .models import (
    Shift, AttendanceRecord, AttendanceLog,
    AttendanceEdit, Leave, Holiday, LeaveType
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

@login_required
def mark_attendance(request):
    """View for manual attendance marking"""
    return render(request, 'attendance/mark_attendance.html')

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

@login_required
def attendance_detail_view(request):
    """View for displaying and editing attendance details"""
    try:
        personnel_id = request.GET.get('personnel_id')
        date_str = request.GET.get('date')
        
        if not personnel_id or not date_str:
            raise Http404("Missing required parameters")
            
        try:
            # Parse the date from the URL
            date = datetime.strptime(date_str.strip(), '%b %d, %Y').date()
        except ValueError:
            raise Http404("Invalid date format")
            
        try:
            employee = Employee.objects.get(employee_number=personnel_id)
        except Employee.DoesNotExist:
            raise Http404("Employee not found")

        # Get or create the attendance log
        log, created = AttendanceLog.objects.get_or_create(
            employee=employee,
            date=date,
            defaults={
                'source': 'Web Interface'
            }
        )
            
        # Get all raw attendance records for this employee on this date
        attendance_records = AttendanceRecord.objects.filter(
            employee=log.employee,
            timestamp__date=date,
            is_active=True
        ).order_by('timestamp')
        
        # Calculate statistics
        total_hours = timedelta()
        status = 'Absent'
        is_late = False
        first_in = None
        last_out = None
        
        # Default shift start time (8:00 AM)
        shift_start = time(8, 0)  # Using datetime.time
        
        records = []
        if attendance_records:
            # First record of the day is IN, last is OUT
            first_record = attendance_records.first()
            last_record = attendance_records.last()
            
            # Set first IN
            first_in = first_record.timestamp.time()
            is_late = first_in > shift_start
            status = 'Late' if is_late else 'Present'
            
            # Set last OUT
            last_out = last_record.timestamp.time()
            
            # Calculate total hours from first IN to last OUT
            if first_in and last_out:
                in_datetime = datetime.combine(date, first_in)
                out_datetime = datetime.combine(date, last_out)
                
                # Handle case where checkout is next day
                if out_datetime < in_datetime:
                    out_datetime += timedelta(days=1)
                    
                total_hours = out_datetime - in_datetime
            
            # Prepare records for template, alternating between IN and OUT
            for i, record in enumerate(attendance_records):
                # First record is IN, last record is OUT, others alternate
                if record == first_record:
                    record_type = 'IN'
                    is_special = True
                    badge_class = 'bg-primary'
                    label = ' (First)'
                elif record == last_record:
                    record_type = 'OUT'
                    is_special = True
                    badge_class = 'bg-primary'
                    label = ' (Last)'
                else:
                    # Alternate between IN and OUT for middle records
                    record_type = 'IN' if i % 2 == 0 else 'OUT'
                    is_special = False
                    badge_class = 'bg-success' if record_type == 'IN' else 'bg-danger'
                    label = ''
                
                records.append({
                    'id': record.id,
                    'time': record.timestamp.strftime('%I:%M %p'),
                    'type': record_type,
                    'label': label,
                    'source': record.event_description or '-',
                    'device_name': record.device_name or '-',
                    'is_special': is_special,
                    'badge_class': badge_class
                })
        
        # Format total hours as decimal
        total_hours_decimal = total_hours.total_seconds() / 3600
        
        context = {
            'log': log,
            'employee_name': log.employee.get_full_name(),
            'personnel_id': log.employee.employee_number,
            'department': log.employee.department.name if log.employee.department else '-',
            'designation': log.employee.designation or '-',
            'date': date.strftime('%b %d, %Y'),
            'day': date.strftime('%A'),
            'records': records,
            'stats': {
                'total_hours': f"{total_hours_decimal:.2f}",
                'is_late': is_late,
                'status': status,
                'first_in': first_in.strftime('%I:%M %p') if first_in else '-',
                'last_out': last_out.strftime('%I:%M %p') if last_out else '-',
            }
        }
            
        return render(request, 'attendance/attendance_detail.html', context)
        
    except AttendanceLog.DoesNotExist:
        raise Http404("Attendance log not found")

@login_required
def attendance_report(request):
    """View for displaying attendance reports and analytics"""
    context = {
        'departments': Department.objects.all()
    }
    return render(request, 'attendance/attendance_report.html', context)

@login_required
def holiday_list(request):
    """View for displaying list of holidays"""
    holidays = Holiday.objects.all().order_by('-date')
    context = {
        'holidays': holidays
    }
    return render(request, 'attendance/holiday_list.html', context)

@login_required
def holiday_create(request):
    """View for creating new holidays"""
    if request.method == 'POST':
        # Handle form submission
        name = request.POST.get('name')
        date = request.POST.get('date')
        description = request.POST.get('description')
        is_recurring = request.POST.get('is_recurring', False)
        
        Holiday.objects.create(
            name=name,
            date=date,
            description=description,
            is_recurring=is_recurring
        )
        return redirect('attendance:holiday_list')
    
    return render(request, 'attendance/holiday_create.html')

@login_required
def recurring_holidays(request):
    """View for managing recurring holidays"""
    holidays = Holiday.objects.filter(is_recurring=True).order_by('-date')
    context = {
        'holidays': holidays
    }
    return render(request, 'attendance/recurring_holidays.html', context)

@login_required
def leave_balance(request):
    """View for showing employee leave balances"""
    employee = None  # Initialize employee to None
    try:
        employee = request.user.employee
    except AttributeError:
        messages.error(request, "No employee record found for your user account. Please contact HR.")
        return redirect('attendance:attendance_list')

    if not employee:
        # Handle the case where employee is None
        messages.error(request, "No employee record found for your user account. Please contact HR.")
        return redirect('attendance:attendance_list')

    leave_types = LeaveType.objects.all()
    balances = []
    
    for leave_type in leave_types:
        used_leaves = Leave.objects.filter(
            employee=employee,
            leave_type=leave_type,
            status='APPROVED',
            start_date__year=timezone.now().year
        ).aggregate(
            total_days=models.Sum('days')
        )['total_days'] or 0
        
        remaining = leave_type.days_allowed - used_leaves
        balances.append({
            'leave_type': leave_type,
            'allowed_days': leave_type.days_allowed,
            'used_days': used_leaves,
            'remaining_days': remaining
        })
    
    context = {
        'balances': balances
    }
    return render(request, 'attendance/leave_balance.html', context)

@login_required
def leave_types(request):
    """View for managing leave types"""
    leave_types = LeaveType.objects.all().order_by('name')
    context = {
        'leave_types': leave_types
    }
    return render(request, 'attendance/leave_types.html', context)

@login_required
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
            records_created, duplicates, total_records, new_employees, unique_dates = process_attendance_excel(excel_file)
            
            # Process logs for each unique date in the uploaded file
            logs_created = 0
            for date in unique_dates:
                logs_created += process_daily_attendance(date)

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

from rest_framework.pagination import PageNumberPagination

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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

# API Views
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
@permission_classes([IsAuthenticated])
def attendance_detail_api(request):
    """API endpoint for getting attendance details"""
    try:
        personnel_id = request.GET.get('personnel_id')
        date_str = request.GET.get('date')
        
        if not personnel_id or not date_str:
            return Response({'error': 'Missing required parameters'}, status=400)
        
        try:
            date = datetime.strptime(date_str.strip(), '%b %d, %Y').date()
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=400)
            
        employee = Employee.objects.get(employee_number=personnel_id)
        log = AttendanceLog.objects.select_related('employee').get(employee=employee, date=date)
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
            time = request.data.get('time')
            reason = request.data.get('reason')
            
            if not time or not reason:
                return Response({'error': 'Time and reason are required'}, status=400)
                
            # Parse the time string
            try:
                hour, minute = map(int, time.split(':'))
                new_time = datetime.combine(log.date, time(hour, minute))
                
                # Update the appropriate time field based on the record type
                if log.first_in_time and log.first_in_time.time() == time:
                    log.first_in_time = new_time
                elif log.last_out_time and log.last_out_time.time() == time:
                    log.last_out_time = new_time
                    
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
    date = request.data.get('date')
    time = request.data.get('time')
    type = request.data.get('type')
    reason = request.data.get('reason')
    
    if not all([personnel_id, date, time, type, reason]):
        return Response({'error': 'All fields are required'}, status=400)
        
    try:
        employee = Employee.objects.get(employee_number=personnel_id)
        log_date = datetime.strptime(date, '%Y-%m-%d').date()
        hour, minute = map(int, time.split(':'))
        log_time = datetime.combine(log_date, time(hour, minute))
        
        # Get or create attendance log for the date
        log, created = AttendanceLog.objects.get_or_create(
            employee=employee,
            date=log_date,
            defaults={
                'source': 'Manual',
                'device': 'Web Interface'
            }
        )
        
        # Update the appropriate time field
        if type == 'IN':
            log.first_in_time = log_time
        else:
            log.last_out_time = log_time
            
        log.save()
        return Response({'status': 'success'})
        
    except (Employee.DoesNotExist, ValueError) as e:
        return Response({'error': str(e)}, status=400)

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

@api_view(['GET'])
def calendar_events(request):
    """Get attendance events for calendar"""
    try:
        start_str = request.GET.get('start', '')
        end_str = request.GET.get('end', '')
        department = request.GET.get('department')
        employee = request.GET.get('employee')
        
        # Parse dates from ISO format, handling timezone if present
        try:
            # Remove timezone part if present
            start_str = start_str.split('+')[0]
            end_str = end_str.split('+')[0]
            
            # Parse dates
            if 'T' in start_str:
                start_date = datetime.strptime(start_str.split('T')[0], '%Y-%m-%d').date()
            else:
                start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
                
            if 'T' in end_str:
                end_date = datetime.strptime(end_str.split('T')[0], '%Y-%m-%d').date()
            else:
                end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        
        except (ValueError, IndexError):
            return Response({'error': 'Invalid date format. Expected YYYY-MM-DD.'}, status=400)
        
        # Build query for attendance logs
        logs_query = Q(date__range=[start_date, end_date])
        if employee:
            logs_query &= Q(employee_id=employee)
        elif department:
            logs_query &= Q(employee__department_id=department)
            
        # Get attendance logs
        logs = AttendanceLog.objects.filter(
            logs_query
        ).select_related('employee', 'employee__department')
        
        # Convert logs to calendar events
        events = []
        for log in logs:
            if log.first_in_time is None and log.last_out_time is None:
                status = 'Absent'
                color = 'danger'
            elif log.is_late:
                status = 'Late'
                color = 'warning'
            else:
                status = 'Present'
                color = 'success'
            
            title = f"{log.employee.employee_number} - {log.employee.get_full_name()}"
            time_info = ''
            if log.first_in_time:
                time_info += f" (In: {log.first_in_time.strftime('%I:%M %p')}"
                if log.last_out_time:
                    time_info += f", Out: {log.last_out_time.strftime('%I:%M %p')})"
                else:
                    time_info += ")"
            
            # Get attendance details
            attendance_info = {
                'time_in': log.first_in_time.strftime('%I:%M %p') if log.first_in_time else None,
                'time_out': log.last_out_time.strftime('%I:%M %p') if log.last_out_time else None,
                'total_hours': f"{log.total_work_minutes / 60:.2f}" if log.total_work_minutes else None,
                'late_by': f"{log.late_minutes} min" if log.late_minutes else None,
                'early_by': f"{log.early_minutes} min" if log.early_minutes else None
            }

            # Determine event color based on status
            status_colors = {
                'present': 'success',
                'absent': 'danger',
                'late': 'warning',
                'leave': 'info',
                'holiday': 'primary'
            }
            color = status_colors.get(log.status, 'secondary')

            # Build event title
            title = f"{log.employee.employee_number} - {log.employee.get_full_name()}"
            if attendance_info['time_in']:
                title += f" ({attendance_info['time_in']}"
                if attendance_info['time_out']:
                    title += f" - {attendance_info['time_out']}"
                title += ")"

            if log.status == 'late' and attendance_info['late_by']:
                title += f" [Late: {attendance_info['late_by']}]"

            events.append({
                'id': log.id,
                'title': f"{title}",
                'start': log.date.isoformat(),
                'color': color,
                'extendedProps': {
                    'employee_id': log.employee.id,
                    'employee_number': log.employee.employee_number,
                    'employee': log.employee.get_full_name(),
                    'department': log.employee.department.name if log.employee.department else '',
                    'type': 'attendance',
                    'status': log.status,
                    'status_color': color,
                    'attendance_info': attendance_info,
                    'is_late': log.is_late,
                    'early_departure': log.early_departure,
                    'total_work_hours': attendance_info['total_hours']
                }
            })
        
        return Response(events)
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
def attendance_details(request):
    """Get detailed attendance information for a specific log"""
    try:
        personnel_id = request.GET.get('personnel_id')
        date_str = request.GET.get('date')
        
        if not personnel_id or not date_str:
            return Response({'error': 'Missing required parameters'}, status=400)
        
        try:
            date = datetime.strptime(date_str.strip(), '%b %d, %Y').date()
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=400)
            
        employee = Employee.objects.get(employee_number=personnel_id)
        log = AttendanceLog.objects.select_related('employee').get(employee=employee, date=date)
        
        # Get raw attendance records for this date
        records = AttendanceRecord.objects.filter(
            employee=log.employee,
            timestamp__date=log.date,
            is_active=True
        ).order_by('timestamp')
        
        raw_records = []
        for record in records:
            raw_records.append({
                'time': record.timestamp.strftime('%I:%M %p'),
                'device': record.device_name,
                'event_point': record.event_point,
                'description': record.event_description
            })
        
        return Response({
            'log_id': log.id,
            'date': log.date.strftime('%b %d, %Y'),
            'employee': log.employee.get_full_name(),
            'status': 'Late' if log.is_late else ('Present' if log.first_in_time else 'Absent'),
            'source': log.source or '-',
            'original_in': log.original_in_time.strftime('%I:%M %p') if log.original_in_time else '-',
            'original_out': log.original_out_time.strftime('%I:%M %p') if log.original_out_time else '-',
            'current_in': log.first_in_time.strftime('%I:%M %p') if log.first_in_time else '-',
            'current_out': log.last_out_time.strftime('%I:%M %p') if log.last_out_time else '-',
            'raw_records': raw_records
        })
    except AttendanceLog.DoesNotExist:
        return Response({'error': 'Log not found'}, status=404)
