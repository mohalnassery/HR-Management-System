from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from employees.models import Employee, Department
from django.db.models import Count

@login_required
def dashboard(request):
    """Dashboard view for authenticated users"""
    context = {
        'total_employees': Employee.objects.count(),
        'total_departments': Department.objects.count(),
        'present_today': 0,  # This will be implemented with attendance tracking
        'on_leave': 0,  # This will be implemented with leave management
    }
    return render(request, 'core/dashboard.html', context)
