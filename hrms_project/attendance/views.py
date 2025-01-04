from django.shortcuts import render
from django.contrib.auth.decorators import login_required

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
