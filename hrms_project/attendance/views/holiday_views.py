from datetime import datetime, date, timedelta, time
from typing import List, Dict, Any

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.contrib import messages
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
    RamadanPeriod
)
from attendance.services import ShiftService, RamadanService
from attendance.serializers import ShiftSerializer, AttendanceRecordSerializer, AttendanceLogSerializer, LeaveSerializer, HolidaySerializer
from attendance.utils import process_attendance_excel, process_daily_attendance, get_attendance_summary


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
        date_str = request.POST.get('date')  # Get date as string
        description = request.POST.get('description')
        is_recurring = request.POST.get('is_recurring', False)

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() # Parse string to date object
            Holiday.objects.create(
                name=name,
                date=date_obj, # Use date object here
                description=description,
                is_recurring=is_recurring,
                created_by=request.user  # Assuming you want to set created_by
            )
            return redirect('attendance:holiday_list')

        except ValueError:
            messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
            return render(request, 'attendance/holiday_create.html') # Re-render form with error

    return render(request, 'attendance/holiday_create.html')


@login_required
def recurring_holidays(request):
    """View for managing recurring holidays"""
    holidays = Holiday.objects.filter(is_recurring=True).order_by('-date')
    context = {
        'holidays': holidays
    }
    return render(request, 'attendance/recurring_holidays.html', context)


class HolidayViewSet(viewsets.ModelViewSet):
    """ViewSet for managing holidays"""
    serializer_class = HolidaySerializer
    permission_classes = [IsAuthenticated]
    queryset = Holiday.objects.all()

    def get_queryset(self):
        return Holiday.objects.filter(is_active=True).order_by('-date')