from datetime import datetime, date, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.db import models  # If you need the models module, import it from django.db
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Leave, LeaveType, LeaveBalance
from ..serializers import LeaveSerializer
from employees.models import Employee

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
        leave_balance = LeaveBalance.objects.filter(employee=employee, leave_type=leave_type).first()
        if leave_balance:  # Check if balance exists
            balances.append({
                'leave_type': leave_type,
                'allowed_days': leave_type.days_allowed,
                'used_days': leave_balance.used_days,
                'remaining_days': leave_balance.available_days
            })
        else:
             balances.append({ # Handle case where LeaveBalance does not exist.
                'leave_type': leave_type,
                'allowed_days': leave_type.days_allowed,
                'used_days': 0,
                'remaining_days': leave_type.days_allowed
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


class LeaveViewSet(viewsets.ModelViewSet):
    """ViewSet for managing leave requests"""
    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]
    queryset = Leave.objects.all()

    def get_queryset(self):
        queryset = Leave.objects.filter(is_active=True)
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset