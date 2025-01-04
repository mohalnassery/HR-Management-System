from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def payroll_list(request):
    """List payroll records"""
    return render(request, 'payroll/payroll_list.html')

@login_required
def generate_payroll(request):
    """Generate payroll"""
    return render(request, 'payroll/generate_payroll.html')

@login_required
def payslip_detail(request, pk):
    """View payslip details"""
    return render(request, 'payroll/payslip_detail.html')

@login_required
def payroll_settings(request):
    """Manage payroll settings"""
    return render(request, 'payroll/payroll_settings.html')
