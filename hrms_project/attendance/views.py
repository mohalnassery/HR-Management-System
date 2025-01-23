from django.shortcuts import render, get_object_or_404
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
from .models import Shift, Attendance, Leave, Holiday
from .serializers import (
    ShiftSerializer, AttendanceSerializer,
    LeaveSerializer, HolidaySerializer
)
from .utils import (
    process_attendance_excel, validate_attendance_edit,
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
def attendance_detail_view(request, attendance_id):
    """View for displaying and editing attendance details"""
    try:
        attendance = Attendance.objects.select_related('employee', 'employee__department').get(id=attendance_id)
        personnel_id = request.GET.get('personnel_id')
        date_str = request.GET.get('date')
        
        if not personnel_id or not date_str:
            raise Http404("Missing required parameters")
            
        try:
            # Parse the date from the URL
            date = datetime.strptime(date_str.strip(), '%b %d, %Y').date()
        except ValueError:
            raise Http404("Invalid date format")
            
        # Verify this attendance record belongs to the correct employee and date
        if str(attendance.employee.employee_number) != str(personnel_id) or attendance.date != date:
            raise Http404("Invalid attendance record")
        
        # Calculate total hours
        total_hours = timedelta()
        if attendance.first_in_time and attendance.last_out_time:
            in_datetime = datetime.combine(date, attendance.first_in_time)
            out_datetime = datetime.combine(date, attendance.last_out_time)
            
            # Handle case where checkout is next day
            if out_datetime < in_datetime:
                out_datetime += timedelta(days=1)
                
            total_hours = out_datetime - in_datetime
        
        # Format total hours as decimal
        total_hours_decimal = total_hours.total_seconds() / 3600
        
        # Default shift start time (8:00 AM)
        shift_start = time(8, 0)
        is_late = attendance.first_in_time > shift_start if attendance.first_in_time else False
        status = 'Late' if is_late else ('Present' if attendance.first_in_time else 'Absent')
        
        context = {
            'attendance': attendance,
            'employee_name': attendance.employee.get_full_name(),
            'personnel_id': attendance.employee.employee_number,
            'department': attendance.employee.department.name if attendance.employee.department else '-',
            'designation': attendance.employee.designation or '-',
            'date': date.strftime('%b %d, %Y'),
            'day': date.strftime('%A'),
            'stats': {
                'total_hours': f"{total_hours_decimal:.2f}",
                'is_late': is_late,
                'status': status,
                'first_in': attendance.first_in_time.strftime('%I:%M %p') if attendance.first_in_time else '-',
                'last_out': attendance.last_out_time.strftime('%I:%M %p') if attendance.last_out_time else '-',
            },
            'edit_history': {
                'original_in': attendance.original_first_in.strftime('%I:%M %p') if attendance.original_first_in else '-',
                'original_out': attendance.original_last_out.strftime('%I:%M %p') if attendance.original_last_out else '-',
                'edited_by': attendance.edited_by.get_full_name() if attendance.edited_by else '-',
                'edit_timestamp': attendance.edit_timestamp.strftime('%b %d, %Y %I:%M %p') if attendance.edit_timestamp else '-',
                'edit_reason': attendance.edit_reason or '-'
            }
        }
            
        return render(request, 'attendance/attendance_detail.html', context)
        
    except Attendance.DoesNotExist:
        raise Http404("Attendance record not found")

# API ViewSets
class ShiftViewSet(viewsets.ModelViewSet):
    """ViewSet for managing shifts"""
    serializer_class = ShiftSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Shift.objects.filter(is_active=True)

class AttendanceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing attendance records with comprehensive functionality"""
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    queryset = Attendance.objects.all()

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def upload_excel(self, request):
        """Handle Excel file upload"""
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            excel_file = request.FILES['file']
            records_created = process_attendance_excel(excel_file)
            
            return Response({
                'message': 'File processed successfully',
                'records_created': records_created,
                'success': True
            })
        except Exception as e:
            return Response({
                'error': str(e),
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def edit_record(self, request, pk=None):
        """Edit attendance record with validation and tracking"""
        instance = self.get_object()
        edit_data = request.data.get('edit_data', {})
        
        # Validate edit request
        validation_result = validate_attendance_edit(instance, edit_data)
        if not validation_result['valid']:
            return Response({
                'message': validation_result['errors'],
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Update fields
                for field, value in edit_data.items():
                    if hasattr(instance, field):
                        setattr(instance, field, value)
                
                # Add edit tracking info
                instance.edited_by = request.user
                instance.edit_timestamp = datetime.now()
                instance.save()
                
                return Response({
                    'message': 'Record updated successfully',
                    'success': True
                })
        except Exception as e:
            return Response({
                'message': str(e),
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def get_summary(self, request):
        """Get attendance summary for specified parameters"""
        try:
            employee_id = request.query_params.get('employee')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            if not all([employee_id, start_date, end_date]):
                return Response({
                    'message': 'Missing required parameters',
                    'success': False
                }, status=status.HTTP_400_BAD_REQUEST)
                
            summary = get_attendance_summary(employee_id, start_date, end_date)
            return Response(summary)
        except Exception as e:
            return Response({
                'message': str(e),
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)

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

class AttendanceListViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for listing attendance records with filtering"""
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    queryset = Attendance.objects.select_related('employee').all()
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
                queryset = queryset.filter(first_in_time__gt=time(8, 0))
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
    """Get attendance events for calendar view"""
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    if not start_date or not end_date:
        return Response({'error': 'Start and end dates are required'}, status=400)
        
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        attendance_records = Attendance.objects.filter(
            date__range=[start, end]
        ).select_related('employee')
        
        events = []
        for record in attendance_records:
            status = 'Present'
            color = '#28a745'  # green
            
            if not record.first_in_time:
                status = 'Absent'
                color = '#dc3545'  # red
            elif record.first_in_time.hour >= 8:  # Assuming 8 AM is the cutoff for late
                status = 'Late'
                color = '#ffc107'  # yellow
                
            events.append({
                'id': record.id,
                'title': f"{record.employee.get_full_name()} - {status}",
                'start': record.date.isoformat(),
                'end': record.date.isoformat(),
                'color': color,
                'extendedProps': {
                    'employee_id': record.employee.id,
                    'status': status,
                    'first_in': record.first_in_time.strftime('%I:%M %p') if record.first_in_time else None,
                    'last_out': record.last_out_time.strftime('%I:%M %p') if record.last_out_time else None
                }
            })
            
        return Response(events)
    except ValueError:
        return Response({'error': 'Invalid date format'}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_employees(request):
    """Search employees by ID or name"""
    search_term = request.GET.get('q', '').strip()
    if not search_term:
        return Response([])
        
    employees = Employee.objects.filter(
        Q(employee_number__icontains=search_term) |
        Q(first_name__icontains=search_term) |
        Q(last_name__icontains=search_term)
    )[:10]
    
    results = []
    for emp in employees:
        results.append({
            'id': emp.id,
            'text': f"{emp.employee_number} - {emp.get_full_name()}",
            'employee_number': emp.employee_number,
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
def attendance_detail_api(request, log_id):
    """API endpoint for getting attendance details"""
    try:
        log = AttendanceLog.objects.select_related('employee').get(id=log_id)
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
    if len(query) < 2:
        return Response([])
    
    employees = Employee.objects.filter(
        Q(employee_number__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    )[:10]  # Limit to 10 results
    
    return Response([{
        'id': emp.id,
        'employee_number': emp.employee_number,
        'full_name': emp.get_full_name()
    } for emp in employees])

@api_view(['GET'])
def calendar_events(request):
    """Get attendance events for calendar"""
    employee_id = request.GET.get('employee_id')
    start_str = request.GET.get('start', '')
    end_str = request.GET.get('end', '')
    
    if not all([employee_id, start_str, end_str]):
        return Response([])
    
    try:
        # Parse ISO format dates
        start_date = parse_datetime(start_str).date()
        end_date = parse_datetime(end_str).date()
        
        if not start_date or not end_date:
            return Response({'error': 'Invalid date format'}, status=400)
            
        # Get attendance logs for the date range
        logs = AttendanceLog.objects.filter(
            employee_id=employee_id,
            date__range=[start_date, end_date]
        ).select_related('employee')
        
        events = []
        for log in logs:
            status = 'Present'
            color = '#28a745'  # Green for present
            
            if not log.first_in_time:
                status = 'Absent'
                color = '#dc3545'  # Red for absent
            elif log.is_late:
                status = 'Late'
                color = '#ffc107'  # Yellow for late
                
            events.append({
                'id': log.id,
                'title': f"{status} ({log.first_in_time.strftime('%I:%M %p') if log.first_in_time else 'No In'} - {log.last_out_time.strftime('%I:%M %p') if log.last_out_time else 'No Out'})",
                'start': log.date.isoformat(),
                'color': color,
                'extendedProps': {
                    'status': status,
                    'first_in': log.first_in_time.strftime('%I:%M %p') if log.first_in_time else '-',
                    'last_out': log.last_out_time.strftime('%I:%M %p') if log.last_out_time else '-',
                    'total_hours': log.total_hours if log.total_hours else '0.00'
                }
            })
        
        return Response(events)
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
def attendance_details(request, log_id):
    """Get detailed attendance information for a specific log"""
    try:
        log = AttendanceLog.objects.select_related('employee').get(id=log_id)
        
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
