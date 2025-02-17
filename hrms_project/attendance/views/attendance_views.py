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
from attendance.serializers import (
    ShiftSerializer, AttendanceRecordSerializer, AttendanceLogSerializer,
    LeaveSerializer, HolidaySerializer
)
from attendance.utils import process_attendance_excel, process_daily_attendance, get_attendance_summary


@login_required
def attendance_list(request):
    """Display attendance list page"""
    context = {
        'departments': Department.objects.all()
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
def attendance_detail_view(request):
    """View for displaying and editing attendance details"""
    try:
        personnel_id = request.GET.get('personnel_id')
        date_str = request.GET.get('date')
        
        if not personnel_id or not date_str:
            raise Http404("Missing required parameters")
            
        try:
            # Try parsing YYYY-MM-DD format first
            date = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
        except ValueError:
            try:
                # Fallback to MMM DD, YYYY format
                date = datetime.strptime(date_str.strip(), '%b %d, %Y').date()
            except ValueError:
                raise Http404("Invalid date format. Expected YYYY-MM-DD or MMM DD, YYYY")
            
        try:
            employee = Employee.objects.get(employee_number=personnel_id)
        except Employee.DoesNotExist:
            raise Http404("Employee not found")

        # Get or create the attendance log
        log, created = AttendanceLog.objects.get_or_create(
            employee=employee,
            date=date,
            defaults={
                'source': 'manual'
            }
        )
            
        # Get all raw attendance records for this employee on this date
        attendance_records = AttendanceRecord.objects.filter(
            employee=log.employee,
            timestamp__date=date,
            is_active=True
        ).order_by('timestamp')
        
        # Get the employee's shift for this date
        shift = ShiftService.get_employee_current_shift(employee)
        shift_start = shift.start_time if shift else time(8, 0)  # Default to 8 AM
        shift_end = shift.end_time if shift else time(17, 0)  # Default to 5 PM
        
        # Calculate statistics
        total_hours = timedelta()
        status = log.status
        is_late = log.is_late
        first_in = None
        last_out = None
        
        records = []
        if attendance_records:
            # First record of the day is IN, last is OUT
            first_record = attendance_records.first()
            last_record = attendance_records.last()
            
            if first_record:
                first_in = first_record.timestamp
                records.append({
                    'id': first_record.id,
                    'time': first_record.timestamp.strftime('%I:%M %p'),
                    'type': 'IN',
                    'label': ' (First)',
                    'source': first_record.event_description or '-',
                    'device_name': first_record.device_name or '-',
                    'is_special': True,
                    'badge_class': 'bg-primary'
                })
            
            if last_record and last_record != first_record:
                last_out = last_record.timestamp
                records.append({
                    'id': last_record.id,
                    'time': last_record.timestamp.strftime('%I:%M %p'),
                    'type': 'OUT',
                    'label': ' (Last)',
                    'source': last_record.event_description or '-',
                    'device_name': last_record.device_name or '-',
                    'is_special': True,
                    'badge_class': 'bg-primary'
                })
                
                if first_in and last_out:
                    total_hours = last_out - first_in
        
        # Format total hours as decimal
        total_hours_decimal = total_hours.total_seconds() / 3600
        
        context = {
            'employee_name': employee.get_full_name(),
            'personnel_id': employee.employee_number,
            'department': employee.department.name if employee.department else '-',
            'designation': employee.designation or '-',
            'date': date.strftime('%b %d, %Y'),
            'day': date.strftime('%A'),
            'records': records,
            'stats': {
                'total_hours': f"{total_hours_decimal:.2f}",
                'is_late': is_late,
                'status': status.title(),
                'first_in': first_in.strftime('%I:%M %p') if first_in else '-',
                'last_out': last_out.strftime('%I:%M %p') if last_out else '-',
            }
        }
        
        return render(request, 'attendance/attendance_detail.html', context)
        
    except Exception as e:
        if settings.DEBUG:
            raise e
        messages.error(request, "An error occurred while retrieving attendance details")
        return redirect('attendance:attendance_list')


@login_required
def attendance_report(request):
    """View for displaying attendance reports and analytics"""
    context = {
        'departments': Department.objects.all()
    }
    return render(request, 'attendance/attendance_report.html', context)


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
            # process_daily_attendance function is assumed to be in utils.py
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
        # get_attendance_summary function is assumed to be in utils.py
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
