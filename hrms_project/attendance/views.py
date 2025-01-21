from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
import pandas as pd
import tempfile
import os

from .models import (
    Shift, AttendanceRecord, AttendanceLog,
    AttendanceEdit, Leave, Holiday
)
from .serializers import (
    ShiftSerializer, AttendanceRecordSerializer,
    AttendanceLogSerializer, AttendanceEditSerializer,
    LeaveSerializer, HolidaySerializer,
    AttendanceUploadSerializer, BulkAttendanceCreateSerializer
)
from .utils import (
    process_attendance_excel, generate_attendance_log,
    process_daily_attendance, validate_attendance_edit,
    get_attendance_summary
)

class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Shift.objects.filter(is_active=True)
        return queryset

class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def upload_excel(self, request):
        serializer = AttendanceUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            excel_file = request.FILES['file']
            
            # Save the file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                for chunk in excel_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                # Process the Excel file
                records_created = process_attendance_excel(temp_file_path)
                
                # Clean up the temporary file
                os.unlink(temp_file_path)
                
                # Process daily attendance
                logs_created = process_daily_attendance()
                
                return Response({
                    'message': 'File processed successfully',
                    'records_created': records_created,
                    'logs_created': logs_created
                })
                
            except Exception as e:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class AttendanceLogViewSet(viewsets.ModelViewSet):
    queryset = AttendanceLog.objects.all()
    serializer_class = AttendanceLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = AttendanceLog.objects.filter(is_active=True)
        employee_id = self.request.query_params.get('employee', None)
        date = self.request.query_params.get('date', None)
        
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if date:
            queryset = queryset.filter(date=date)
        
        return queryset

    @action(detail=True, methods=['post'])
    def edit_attendance(self, request, pk=None):
        attendance_log = self.get_object()
        
        try:
            edited_in_time = request.data.get('first_in_time')
            edited_out_time = request.data.get('last_out_time')
            edit_reason = request.data.get('reason')
            
            if not edit_reason:
                return Response(
                    {'error': 'Edit reason is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate edit times
            validate_attendance_edit(
                attendance_log,
                edited_in_time,
                edited_out_time
            )
            
            with transaction.atomic():
                # Create attendance edit record
                AttendanceEdit.objects.create(
                    attendance_log=attendance_log,
                    original_first_in=attendance_log.first_in_time,
                    original_last_out=attendance_log.last_out_time,
                    edited_first_in=edited_in_time,
                    edited_last_out=edited_out_time,
                    edited_by=request.user,
                    edit_reason=edit_reason
                )
                
                # Update attendance log
                attendance_log.first_in_time = edited_in_time
                attendance_log.last_out_time = edited_out_time
                attendance_log.source = 'manual'
                attendance_log.save()
            
            return Response({
                'message': 'Attendance updated successfully'
            })
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LeaveViewSet(viewsets.ModelViewSet):
    queryset = Leave.objects.all()
    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Leave.objects.filter(is_active=True)
        employee_id = self.request.query_params.get('employee', None)
        status = self.request.query_params.get('status', None)
        
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset

    @action(detail=True, methods=['post'])
    def approve_leave(self, request, pk=None):
        leave = self.get_object()
        action = request.data.get('action')
        
        if action not in ['approve', 'reject']:
            return Response(
                {'error': 'Invalid action'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        leave.status = 'approved' if action == 'approve' else 'rejected'
        leave.approved_by = request.user
        leave.save()
        
        return Response({'message': f'Leave {leave.status} successfully'})

class HolidayViewSet(viewsets.ModelViewSet):
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Holiday.objects.filter(is_active=True)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_employee_attendance(request, employee_id):
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    try:
        from employees.models import Employee
        employee = get_object_or_404(Employee, id=employee_id)
        
        if not start_date or not end_date:
            return Response(
                {'error': 'Start date and end date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        summary = get_attendance_summary(employee, start_date, end_date)
        return Response(summary)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@login_required
def attendance_list(request):
    """List attendance records"""
    return render(request, 'attendance/attendance_list.html')

@login_required
def mark_attendance(request):
    """Mark attendance"""
    return render(request, 'attendance/mark_attendance.html')

@login_required
def leave_request_list(request):
    """List leave requests"""
    return render(request, 'attendance/leave_request_list.html')

@login_required
def leave_request_create(request):
    """Create leave request"""
    return render(request, 'attendance/leave_request_form.html')

@login_required
def leave_request_detail(request, pk):
    """View leave request details"""
    return render(request, 'attendance/leave_request_detail.html')
