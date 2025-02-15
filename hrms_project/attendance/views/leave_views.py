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

from ..models import Leave, LeaveType, LeaveBalance, LeaveBeginningBalance
from ..serializers import LeaveSerializer
from ..forms import LeaveBalanceUploadForm
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
    """View for showing employee leave balances and handling beginning balance imports"""
    from employees.models import Employee, Department
    from django.db.models import Q
    
    # Get query parameters
    selected_department = request.GET.get('department')
    selected_employee = request.GET.get('employee')
    search_query = request.GET.get('search', '').strip()
    
    # Initialize employee
    employee = None
    
    # For staff users, allow employee selection
    if request.user.is_staff:
        # Get departments and employees for filters
        departments = Department.objects.all().order_by('name')
        employees_query = Employee.objects.all()
        
        # Filter employees by department if selected
        if selected_department:
            employees_query = employees_query.filter(department_id=selected_department)
            
        # Filter by search query (employee number or name)
        if search_query:
            employees_query = employees_query.filter(
                Q(employee_number__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
            
        # Get selected employee if any
        if selected_employee:
            try:
                employee = employees_query.get(id=selected_employee)
            except Employee.DoesNotExist:
                messages.error(request, "Selected employee not found.")
                
        employees = employees_query.order_by('first_name', 'last_name')
    else:
        # For regular users, only show their own balances
        try:
            employee = request.user.employee
        except AttributeError:
            messages.error(request, "No employee record found for your user account. Please contact HR.")
            return redirect('attendance:attendance_list')
        
        departments = []
        employees = []

    # Handle CSV upload for beginning balances
    if request.method == 'POST':
        form = LeaveBalanceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                csv_file = request.FILES['csv_file']
                as_of_date = form.cleaned_data['as_of_date']
                leave_type_code = form.cleaned_data['leave_type_code']
                
                # Get the leave type
                leave_type = get_object_or_404(LeaveType, code=leave_type_code)
                
                # Process CSV file
                import csv
                from io import TextIOWrapper
                decoded_file = TextIOWrapper(csv_file.file, encoding='utf-8')
                reader = csv.DictReader(decoded_file)
                
                success_count = 0
                error_count = 0
                for row in reader:
                    try:
                        emp_number = row['employee_number']
                        balance = float(row['leave_balance'])
                        
                        # Get employee by number
                        emp = Employee.objects.get(employee_number=emp_number)
                        
                        # Create or update beginning balance
                        LeaveBeginningBalance.objects.update_or_create(
                            employee=emp,
                            leave_type=leave_type,
                            as_of_date=as_of_date,
                            defaults={'balance_days': balance}
                        )
                        success_count += 1
                    except (Employee.DoesNotExist, KeyError, ValueError) as e:
                        error_count += 1
                        continue
                
                messages.success(request, f"Successfully processed {success_count} records. {error_count} records had errors.")
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
    else:
        form = LeaveBalanceUploadForm()

    # Get all leave types and balances
    leave_types = LeaveType.objects.all()
    balances = []
    
    # Get beginning balances based on selected employee or user
    if request.user.is_staff:
        if employee:
            beginning_balances = LeaveBeginningBalance.objects.filter(
                employee=employee
            ).select_related('leave_type', 'employee').order_by('-as_of_date')
        else:
            beginning_balances = LeaveBeginningBalance.objects.all().select_related('leave_type', 'employee').order_by('-as_of_date')
    else:
        beginning_balances = LeaveBeginningBalance.objects.filter(
            employee=employee
        ).select_related('leave_type').order_by('-as_of_date')

    # Initialize or get leave balances
    target_employee = employee if employee else request.user.employee if not request.user.is_staff else None
    
    if target_employee:
        # Initialize leave balances if they don't exist
        for leave_type in leave_types:
            LeaveBalance.objects.get_or_create(
                employee=target_employee,
                leave_type=leave_type,
                defaults={
                    'total_days': leave_type.days_allowed,
                    'used_days': 0
                }
            )
        
        # Get balances for the target employee
        for leave_type in leave_types:
            leave_balance = LeaveBalance.objects.filter(employee=target_employee, leave_type=leave_type).first()
            if leave_balance:  # Check if balance exists
                balances.append({
                    'leave_type': leave_type,
                    'total_days': leave_type.days_allowed,
                    'used_days': leave_balance.used_days,
                    'remaining_days': leave_balance.available_days
                })
            else:
                balances.append({ # Handle case where LeaveBalance does not exist.
                    'leave_type': leave_type,
                    'total_days': leave_type.days_allowed,
                    'used_days': 0,
                    'remaining_days': leave_type.days_allowed
                })

    # Add context for template
    context = {
        'form': form,
        'balances': balances,
        'beginning_balances': beginning_balances,
        'departments': departments,
        'employees': employees,
        'selected_department': selected_department,
        'selected_employee': selected_employee
    }

    return render(request, 'attendance/leave_balance.html', context)


    context = {
        'balances': balances,
        'form': form,
        'beginning_balances': beginning_balances
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