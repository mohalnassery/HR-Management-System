from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import transaction
from django.urls import reverse
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..serializers import ShiftSerializer

from attendance.models import Shift, ShiftAssignment # ADD THESE TWO LINES
# from attendance.serializers import ShiftOverlapSerializer # Uncomment if you will use ShiftOverlapSerializer
from employees.models import Employee


class ShiftViewSet(viewsets.ModelViewSet):
    """ViewSet for managing shifts through the API"""
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [IsAuthenticated]


@login_required
def shift_list(request):
    """View for listing all shifts"""
    shifts = Shift.objects.all().order_by('start_time')
    return render(request, 'attendance/shifts/shift_list.html', {'shifts': shifts})

@login_required
def shift_create(request):
    """View for creating a new shift"""
    if request.method == 'POST':
        name = request.POST.get('name')
        shift_type = request.POST.get('shift_type')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        is_night_shift = request.POST.get('is_night_shift') == 'on'
        grace_period = int(request.POST.get('grace_period', 15))
        break_duration = int(request.POST.get('break_duration', 60))

        # Handle night shift timing fields
        default_night_start_time = request.POST.get('default_night_start_time')
        default_night_end_time = request.POST.get('default_night_end_time')

        shift = Shift.objects.create(
            name=name,
            shift_type=shift_type,
            start_time=start_time,
            end_time=end_time,
            is_night_shift=is_night_shift,
            grace_period=grace_period,
            break_duration=break_duration,
            default_night_start_time=default_night_start_time if default_night_start_time else None,
            default_night_end_time=default_night_end_time if default_night_end_time else None
        )
        messages.success(request, 'Shift created successfully.')
        return redirect('attendance:shift_list')

    context = {
        'shift_types': Shift.SHIFT_TYPES # Pass SHIFT_TYPES to context
    }
    return render(request, 'attendance/shifts/shift_form.html', context) # Pass context here

@login_required
def shift_edit(request, pk):
    """View for editing an existing shift"""
    shift = get_object_or_404(Shift, pk=pk)

    if request.method == 'POST':
        # Update basic fields
        shift.name = request.POST.get('name')
        shift.shift_type = request.POST.get('shift_type')
        shift.start_time = request.POST.get('start_time')
        shift.end_time = request.POST.get('end_time')
        shift.is_night_shift = request.POST.get('is_night_shift') == 'on'
        shift.grace_period = int(request.POST.get('grace_period', 15))
        shift.break_duration = int(request.POST.get('break_duration', 60))

        # Update night shift timing fields
        default_night_start_time = request.POST.get('default_night_start_time')
        default_night_end_time = request.POST.get('default_night_end_time')
        shift.default_night_start_time = default_night_start_time if default_night_start_time else None
        shift.default_night_end_time = default_night_end_time if default_night_end_time else None
        shift.save()

        messages.success(request, 'Shift updated successfully.')
        return redirect('attendance:shift_list')

    context = {
        'shift': shift,
        'shift_types': Shift.SHIFT_TYPES # Pass SHIFT_TYPES to context
    }
    return render(request, 'attendance/shifts/shift_form.html', context) # Pass context here

@login_required
def shift_assignment_list(request):
    """View for listing shift assignments"""
    assignments = ShiftAssignment.objects.select_related(
        'employee', 'shift'
    ).order_by('-start_date')
    
    paginator = Paginator(assignments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'attendance/shifts/assignment_list.html', {
        'page_obj': page_obj
    })

@login_required
def shift_assignment_create(request):
    """View for creating a new shift assignment"""
    if request.method == 'POST':
        # Get comma-separated employee IDs and split them
        employee_ids = request.POST.get('employee[]', '').split(',')
        if not employee_ids or not employee_ids[0]:  # Check if the list is empty or contains only empty string
            messages.error(request, 'Please select at least one employee.')
            return redirect('attendance:shift_assignment_create')
        shift_id = request.POST.get('shift')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date') or None
        is_active = request.POST.get('is_active') == 'on'

        try:
            with transaction.atomic():
                created_count = 0
                for employee_id in employee_ids:
                    # Deactivate any existing active assignments for this employee
                    ShiftAssignment.objects.filter(
                        employee_id=employee_id,
                        is_active=True
                    ).update(is_active=False)

                    # Create new assignment
                    ShiftAssignment.objects.create(
                        employee_id=employee_id,
                        shift_id=shift_id,
                        start_date=start_date,
                        end_date=end_date,
                        is_active=is_active,
                        created_by=request.user
                    )
                    created_count += 1

                messages.success(request, f'{created_count} Shift assignments created successfully.')
                return redirect('attendance:shift_assignment_list')

        except Exception as e:
            messages.error(request, f'Error assigning shift: {str(e)}')

    employees = Employee.objects.filter(is_active=True).select_related('department')
    shifts = Shift.objects.filter(is_active=True)
    # Get unique departments from the employees
    departments = list({emp.department for emp in employees if emp.department})

    return render(request, 'attendance/shifts/assignment_form.html', {
        'employees': employees,
        'shifts': shifts,
        'departments': departments
    })

@login_required
def shift_assignment_edit(request, pk):
    """View for editing a shift assignment"""
    assignment = get_object_or_404(ShiftAssignment, pk=pk)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # If making this assignment active, deactivate other active assignments
                if request.POST.get('is_active') == 'on' and not assignment.is_active:
                    ShiftAssignment.objects.filter(
                        employee=assignment.employee,
                        is_active=True
                    ).exclude(pk=pk).update(is_active=False)

                assignment.shift_id = request.POST.get('shift')
                assignment.start_date = request.POST.get('start_date')
                assignment.end_date = request.POST.get('end_date') or None
                assignment.is_active = request.POST.get('is_active') == 'on'
                assignment.save()

                messages.success(request, 'Shift assignment updated successfully.')
                return redirect('attendance:shift_assignment_list')

        except Exception as e:
            messages.error(request, f'Error updating shift assignment: {str(e)}')

    employees = Employee.objects.filter(is_active=True).select_related('department')
    shifts = Shift.objects.filter(is_active=True)
    # Get unique departments from the employees
    departments = list({emp.department for emp in employees if emp.department})

    return render(request, 'attendance/shifts/assignment_form.html', {
        'form': assignment,
        'employees': employees,
        'shifts': shifts,
        'departments': departments
    })

@login_required
def shift_assignment_delete(request, pk):
    """View for deleting a shift assignment"""
    assignment = get_object_or_404(ShiftAssignment, pk=pk)
    
    try:
        assignment.delete()
        messages.success(request, 'Shift assignment deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting shift assignment: {str(e)}')
    
    return redirect('attendance:shift_assignment_list')

@login_required
def get_employee_shifts(request, employee_id):
    """API endpoint for getting an employee's shift history"""
    assignments = ShiftAssignment.objects.filter(
        employee_id=employee_id
    ).select_related('shift').order_by('-start_date')
    
    data = [{
        'id': a.id,
        'shift_name': a.shift.name,
        'start_date': a.start_date.strftime('%Y-%m-%d'),
        'end_date': a.end_date.strftime('%Y-%m-%d') if a.end_date else None,
        'is_active': a.is_active
    } for a in assignments]
    
    return JsonResponse({'assignments': data})
