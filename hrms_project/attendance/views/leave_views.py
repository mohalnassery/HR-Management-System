from datetime import datetime, date, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from decimal import Decimal
from django.db import models
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ..models import (
    Leave, LeaveType, LeaveBalance, LeaveBeginningBalance,
    AttendanceLog, Holiday, LeaveDocument, LeaveActivity  # Add LeaveActivity to imports
)
from ..services.leave_rule_service import LeaveRuleService
from ..serializers import LeaveSerializer
from ..forms import LeaveBalanceUploadForm, LeaveRequestForm
from employees.models import Employee, Department  # Add Department here

@login_required
def leave_request_list(request):
    """Display leave requests list page"""
    # Initialize query
    leave_requests = Leave.objects.select_related(
        'employee',
        'employee__department',
        'leave_type'
    ).filter(is_active=True)
    
    # For non-staff users, only show their own requests
    if not request.user.is_staff:
        leave_requests = leave_requests.filter(employee=request.user.employee)
    
    # Apply filters if provided
    status = request.GET.get('status')
    leave_type = request.GET.get('leave_type')
    department = request.GET.get('department')
    employee = request.GET.get('employee')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if status:
        leave_requests = leave_requests.filter(status=status)
    if leave_type:
        leave_requests = leave_requests.filter(leave_type__code=leave_type)
    if department and request.user.is_staff:
        leave_requests = leave_requests.filter(employee__department_id=department)
    if employee and request.user.is_staff:
        leave_requests = leave_requests.filter(employee_id=employee)
    if start_date:
        leave_requests = leave_requests.filter(start_date__gte=start_date)
    if end_date:
        leave_requests = leave_requests.filter(end_date__lte=end_date)
    
    # Order by most recent first
    leave_requests = leave_requests.order_by('-created_at')
    
    # Get leave types and departments for filters
    leave_types = LeaveType.objects.filter(is_active=True)
    departments = Department.objects.all() if request.user.is_staff else []
    
    # Get employees for filter (only for staff users)
    employees = []
    if request.user.is_staff:
        employees_query = Employee.objects.all()
        if department:
            employees_query = employees_query.filter(department_id=department)
        employees = employees_query.order_by('first_name', 'last_name')
    
    context = {
        'leave_requests': leave_requests,
        'leave_types': leave_types,
        'departments': departments,
        'employees': employees,
        'selected_employee': employee,  # Pass selected employee ID for maintaining filter state
    }
    
    return render(request, 'attendance/leave_request_list.html', context)

@login_required
def leave_request_create(request):
    """Display leave request creation page and handle form submission"""
    # Get selected employee from query params or POST data
    employee_id = request.GET.get('employee') or request.POST.get('employee')
    employee = None
    leave_balances = None
    departments = None
    employees = None
    
    # For staff users, allow employee selection
    if request.user.is_staff:
        departments = Department.objects.all().order_by('name')
        employees_query = Employee.objects.all()
        
        # Filter by department if provided
        department_id = request.GET.get('department')
        if department_id:
            employees_query = employees_query.filter(department_id=department_id)
        
        # Filter by search query if provided
        search_query = request.GET.get('search', '').strip()
        if search_query:
            employees_query = employees_query.filter(
                Q(employee_number__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        employees = employees_query.order_by('first_name', 'last_name')
        
        if employee_id:
            try:
                employee = employees_query.get(id=employee_id)
                leave_balances = LeaveBalance.objects.filter(employee=employee)
            except Employee.DoesNotExist:
                messages.error(request, "Selected employee not found.")
                return redirect('attendance:leave_request_list')
    else:
        # For regular users, only allow them to request for themselves
        try:
            employee = request.user.employee
            leave_balances = LeaveBalance.objects.filter(employee=employee)
        except AttributeError:
            messages.error(request, "No employee record found for your user account. Please contact HR.")
            return redirect('attendance:leave_request_list')
    
    if request.method == 'POST':
        # Handle AJAX request for updating sub-types
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.POST.get('update_sub_types'):
            form = LeaveRequestForm(request.POST)
            leave_type_id = request.POST.get('leave_type')
            if leave_type_id:
                form.set_sub_type_choices(leave_type_id)
                return JsonResponse({
                    'sub_type_choices': form.fields['leave_sub_type'].choices
                })
            return JsonResponse({'sub_type_choices': []})

        if not employee:
            messages.error(request, "Please select an employee first.")
            return redirect('attendance:leave_request_create')
            
        form = LeaveRequestForm(request.POST, request.FILES)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.employee = employee
            leave_request.status = 'pending'
            
            # Ensure end date is never less than start date
            if leave_request.end_date < leave_request.start_date:
                leave_request.end_date = leave_request.start_date
            
            # Calculate duration based on start and end dates and leave type
            duration = (leave_request.end_date - leave_request.start_date).days + 1
            
            # Adjust duration based on leave sub-type
            leave_sub_type = form.cleaned_data.get('leave_sub_type')
            if leave_sub_type:
                if leave_sub_type in ['half_day', 'morning', 'afternoon']:
                    duration = 0.5
                elif '_' in leave_sub_type:
                    # Extract days from sub-type code (e.g., '3_days' -> 3)
                    try:
                        days = int(leave_sub_type.split('_')[0])
                        duration = days
                    except (ValueError, IndexError):
                        pass
            
            leave_request.duration = duration
            
            # Validate leave request using LeaveRuleService
            is_valid, message, data = LeaveRuleService.validate_leave_request(
                employee=employee,
                leave_type=leave_request.leave_type,
                sub_type=leave_sub_type,
                start_date=leave_request.start_date,
                end_date=leave_request.end_date
            )
            
            if not is_valid:
                messages.error(request, message)
                return render(request, 'attendance/leave_request_form.html', {
                    'form': form,
                    'leave_balances': leave_balances,
                    'departments': departments,
                    'employees': employees,
                    'selected_employee': employee
                })
            
            # If HR admin is creating the request, auto-approve it
            if request.user.is_staff:
                leave_request.status = 'approved'
                leave_request.approved_by = request.user
                leave_request.approved_at = timezone.now()
            
            leave_request.save()
            
            # Create activity record for leave creation
            LeaveActivity.objects.create(
                leave=leave_request,
                actor=request.user,
                action='create',
                details=f"Leave request created by {request.user.get_full_name()}"
            )
            
            # Handle document upload if provided
            if form.cleaned_data.get('document'):
                LeaveDocument.objects.create(
                    leave=leave_request,
                    document=form.cleaned_data['document'],
                    document_type='supporting_document'
                )
            
            messages.success(request, 'Leave request submitted successfully')
            return redirect('attendance:leave_request_list')
    else:
        form = LeaveRequestForm()
    
    # Calculate balance percentages for progress bars
    if leave_balances and employee:
        for balance in leave_balances:
            # Get the leave type
            leave_type = balance.leave_type
            
            # For annual leave types, calculate the balance more accurately
            if leave_type.code in ['ANNUAL', 'HALF']:
                # Get beginning balance
                beginning_balance = LeaveBeginningBalance.objects.filter(
                    employee=employee,
                    leave_type=leave_type
                ).order_by('-as_of_date').first()
                
                initial_balance = beginning_balance.balance_days if beginning_balance else 0
                
                # Get beginning date (try join_date first, then beginning balance, then default to Jan 1st)
                if beginning_balance:
                    start_date = beginning_balance.as_of_date
                else:
                    # Try to get join_date if it exists
                    try:
                        if hasattr(employee, 'join_date') and employee.join_date:
                            start_date = employee.join_date
                        else:
                            # Default to January 1st of current year if no join_date
                            current_year = date.today().year
                            start_date = date(current_year, 1, 1)
                    except AttributeError:
                        # Default to January 1st of current year if join_date field doesn't exist
                        current_year = date.today().year
                        start_date = date(current_year, 1, 1)
                
                end_date = date.today()
                
                try:
                    # Get holidays for the period once
                    holiday_dates = set(Holiday.objects.filter(
                        date__range=[start_date, end_date]
                    ).values_list('date', flat=True))
                    
                    # Get attendance logs for the period
                    attendance_logs = set(AttendanceLog.objects.filter(
                        employee=employee,
                        date__range=[start_date, end_date],
                        status='present'  # Only count present days
                    ).values_list('date', flat=True))
                    
                    # Count Fridays that should be included
                    friday_count = 0
                    current_date = start_date
                    while current_date <= end_date:
                        if current_date.weekday() == 4:  # Friday
                            thursday = current_date - timedelta(days=1)
                            saturday = current_date + timedelta(days=1)
                            
                            # Check if Thursday or Saturday was attended or was a holiday
                            thursday_attended = thursday in attendance_logs or thursday in holiday_dates
                            saturday_attended = saturday in attendance_logs or saturday in holiday_dates
                            
                            if thursday_attended or saturday_attended:
                                friday_count += 1
                        
                        current_date += timedelta(days=1)
                    
                    # Calculate total working days including valid Fridays and holidays
                    total_working_days = Decimal(len(attendance_logs) + friday_count + len(holiday_dates))
                    
                    # Calculate monthly rate (2.5 days per month, assuming 30 working days per month)
                    daily_rate = Decimal('2.5') / Decimal('30')
                    
                    # Calculate accrued leave
                    accrued_days = total_working_days * daily_rate
                    
                    # Get used days from the balance
                    used_days = balance.used_days
                    pending_days = balance.pending_days
                    
                    # Calculate total and remaining days
                    total_days = Decimal(initial_balance) + accrued_days
                    remaining_days = total_days - used_days - pending_days
                    
                    # Update the balance object with calculated values
                    balance.total_days = total_days
                    balance.remaining_days = remaining_days
                    
                except Exception as e:
                    print(f"Error in leave calculation: {str(e)}")
                    # If there's an error in calculation, use the available_days property
                    balance.remaining_days = balance.available_days
                    total_days = balance.total_days
            else:
                # For all other leave types, use the available_days property
                balance.remaining_days = balance.available_days
                total_days = balance.total_days
            
            # Calculate percentage for progress bar
            if total_days > 0:
                balance.balance_percentage = (balance.remaining_days / total_days) * 100
            else:
                balance.balance_percentage = 0
    
    return render(request, 'attendance/leave_request_form.html', {
        'form': form,
        'leave_balances': leave_balances,
        'departments': departments,
        'employees': employees,
        'selected_employee': employee
    })

@login_required
def leave_request_detail(request, pk):
    """Display leave request details page"""
    leave = get_object_or_404(Leave.objects.select_related(
        'employee',
        'employee__department',
        'leave_type',
        'approved_by'
    ), pk=pk)
    
    # Get similar leaves (same type, same employee)
    similar_leaves = Leave.objects.filter(
        employee=leave.employee,
        leave_type=leave.leave_type,
        is_active=True
    ).exclude(
        pk=pk  # Exclude current leave
    ).select_related(
        'employee',
        'leave_type'
    ).order_by('-created_at')
    
    # Get leave balances
    balances = {
        'annual': {'remaining': 0},
        'sick': {'remaining': 0},
        'permission': {'remaining': 0}
    }
    
    try:
        leave_balances = LeaveBalance.objects.filter(
            employee=leave.employee,
            is_active=True
        ).select_related('leave_type')
        
        for balance in leave_balances:
            if balance.leave_type.code == 'ANNUAL':
                balances['annual']['remaining'] = balance.available_days
            elif balance.leave_type.code == 'SICK':
                balances['sick']['remaining'] = balance.available_days
            elif balance.leave_type.code == 'PERMISSION':
                balances['permission']['remaining'] = balance.available_days
    except LeaveBalance.DoesNotExist:
        pass
    
    context = {
        'leave': leave,
        'similar_leaves': similar_leaves,
        'balance': balances
    }
    
    return render(request, 'attendance/leave_request_detail.html', context)


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
            
            if leave_type.code in ['ANNUAL', 'HALF']:  # Special calculation for annual and half-day leaves
                # Get beginning balance
                beginning_balance = LeaveBeginningBalance.objects.filter(
                    employee=target_employee,
                    leave_type=leave_type
                ).order_by('-as_of_date').first()
                
                initial_balance = beginning_balance.balance_days if beginning_balance else 0
                
                # Get beginning date (try join_date first, then beginning balance, then default to Jan 1st)
                if beginning_balance:
                    start_date = beginning_balance.as_of_date
                else:
                    # Try to get join_date if it exists
                    try:
                        if hasattr(target_employee, 'join_date') and target_employee.join_date:
                            start_date = target_employee.join_date
                        else:
                            # Default to January 1st of current year if no join_date
                            current_year = date.today().year
                            start_date = date(current_year, 1, 1)
                    except AttributeError:
                        # Default to January 1st of current year if join_date field doesn't exist
                        current_year = date.today().year
                        start_date = date(current_year, 1, 1)
                    
                end_date = date.today()
                
                try:
                    # Get holidays for the period once
                    holiday_dates = set(Holiday.objects.filter(
                        date__range=[start_date, end_date]
                    ).values_list('date', flat=True))
                    
                    # Get attendance logs for the period
                    attendance_logs = set(AttendanceLog.objects.filter(
                        employee=target_employee,
                        date__range=[start_date, end_date],
                        status='present'  # Only count present days
                    ).values_list('date', flat=True))
                    
                    # Count Fridays that should be included
                    friday_count = 0
                    current_date = start_date
                    while current_date <= end_date:
                        if current_date.weekday() == 4:  # Friday
                            thursday = current_date - timedelta(days=1)
                            saturday = current_date + timedelta(days=1)
                            
                            # Check if Thursday or Saturday was attended or was a holiday
                            thursday_attended = thursday in attendance_logs or thursday in holiday_dates
                            saturday_attended = saturday in attendance_logs or saturday in holiday_dates
                            
                            if thursday_attended or saturday_attended:
                                friday_count += 1
                        
                        current_date += timedelta(days=1)
                    
                    # Calculate total working days including valid Fridays and holidays
                    total_working_days = Decimal(len(attendance_logs) + friday_count + len(holiday_dates))
                    
                    # Calculate monthly rate (2.5 days per month, assuming 30 working days per month)
                    daily_rate = Decimal('2.5') / Decimal('30')
                    
                    # Calculate accrued leave
                    accrued_days = total_working_days * daily_rate
                    
                    # Get used days
                    used_days = leave_balance.used_days if leave_balance else Decimal('0')
                    
                    # Calculate total and remaining days
                    total_days = Decimal(initial_balance) + accrued_days
                    remaining_days = total_days - used_days
                    
                    # Add debug message
                    print(f"Leave calculation for {leave_type.code}:")
                    print(f"Start date: {start_date}, End date: {end_date}")
                    print(f"Working days: {len(attendance_logs)}, Fridays: {friday_count}, Holidays: {len(holiday_dates)}")
                    print(f"Total working days: {total_working_days}")
                    print(f"Daily rate: {daily_rate}, Accrued days: {accrued_days}")
                    print(f"Initial balance: {initial_balance}, Used days: {used_days}")
                    print(f"Total days: {total_days}, Remaining days: {remaining_days}")
                    
                except Exception as e:
                    print(f"Error in leave calculation: {str(e)}")
                    # If there's an error in calculation, use defaults
                    total_days = 0
                    remaining_days = 0
                    used_days = 0
            else:
                # For all other leave types, simply use the allowed days and subtract used days
                total_days = leave_type.days_allowed
                used_days = leave_balance.used_days if leave_balance else 0
                remaining_days = total_days - used_days
            
            balances.append({
                'leave_type': leave_type,
                'total_days': round(total_days, 2),
                'used_days': round(used_days, 2),
                'remaining_days': round(remaining_days, 2)
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

@login_required
@require_POST
def leave_request_action(request, pk, action):
    """Handle leave request actions (approve, reject, cancel, delete)"""
    if action not in ['approve', 'reject', 'cancel', 'delete']:
        return JsonResponse({'error': 'Invalid action'}, status=400)
        
    try:
        leave = Leave.objects.get(pk=pk, is_active=True)
        
        # Check permissions
        if action in ['approve', 'reject', 'delete']:
            if not request.user.is_staff:
                return JsonResponse({'error': 'Permission denied'}, status=403)
        elif action == 'cancel':
            if leave.employee.user != request.user and not request.user.is_staff:
                return JsonResponse({'error': 'Permission denied'}, status=403)
        
        if action == 'delete':
            # Delete all associated leave activities
            LeaveActivity.objects.filter(leave=leave).delete()
            
            # Mark leave as inactive
            leave.is_active = False
            leave.save()
        else:
            # Update leave status
            if action == 'approve':
                leave.status = 'approved'
                leave.approved_by = request.user
                leave.approved_at = timezone.now()
            elif action == 'reject':
                leave.status = 'rejected'
                leave.rejected_by = request.user
                leave.rejected_at = timezone.now()
            else:  # cancel
                leave.status = 'cancelled'
                leave.cancelled_at = timezone.now()
                
            leave.save()
            
            # Create activity record for this action
            LeaveActivity.objects.create(
                leave=leave,
                actor=request.user,
                action=action,
                details=f"Leave request {action}ed by {request.user.get_full_name()}"
            )
            
        return JsonResponse({'status': 'success'})
        
    except Leave.DoesNotExist:
        return JsonResponse({'error': 'Leave request not found'}, status=404)