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
from attendance.forms import HolidayForm


@login_required
def holiday_list(request):
    """View for displaying list of holidays"""
    holidays = Holiday.objects.all().order_by('-date')
    context = {
        'holidays': holidays,
        'title': 'Holidays'
    }
    return render(request, 'attendance/holiday_list.html', context)

@login_required
def holiday_create(request):
    """View for creating new holidays"""
    if request.method == 'POST':
        form = HolidayForm(request.POST)
        if form.is_valid():
            holiday = form.save(commit=False)
            holiday.created_by = request.user
            holiday.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Holiday created successfully.')
            return redirect('attendance:holiday_list')
    else:
        form = HolidayForm()
    
    context = {
        'form': form,
        'title': 'Create Holiday',
        'departments': Department.objects.all()
    }
    return render(request, 'attendance/holiday_form.html', context)


@login_required
def recurring_holidays(request):
    """View for managing recurring holidays"""
    holidays = Holiday.objects.filter(is_recurring=True).order_by('-date')
    departments = Department.objects.all()
    context = {
        'holidays': holidays,
        'departments': departments,
        'title': 'Recurring Holidays'
    }
    return render(request, 'attendance/recurring_holidays.html', context)


@login_required
def holiday_edit(request, pk):
    """View for editing holidays"""
    holiday = get_object_or_404(Holiday, pk=pk)
    
    if request.method == 'POST':
        form = HolidayForm(request.POST, instance=holiday)
        if form.is_valid():
            form.save()
            messages.success(request, 'Holiday updated successfully.')
            return redirect('attendance:holiday_list')
    else:
        form = HolidayForm(instance=holiday)
    
    context = {
        'form': form,
        'holiday': holiday,
        'title': 'Edit Holiday',
        'departments': Department.objects.all()
    }
    return render(request, 'attendance/holiday_form.html', context)


@login_required
def holiday_delete(request, pk):
    """View for deleting holidays"""
    holiday = get_object_or_404(Holiday, pk=pk)
    
    if request.method == 'POST':
        holiday.delete()
        messages.success(request, 'Holiday deleted successfully.')
        return redirect('attendance:holiday_list')
        
    context = {
        'holiday': holiday
    }
    return render(request, 'attendance/holiday_confirm_delete.html', context)


class HolidayViewSet(viewsets.ModelViewSet):
    """ViewSet for managing holidays"""
    serializer_class = HolidaySerializer
    permission_classes = [IsAuthenticated]
    queryset = Holiday.objects.all()

    def get_queryset(self):
        return Holiday.objects.filter(is_active=True).order_by('-date')