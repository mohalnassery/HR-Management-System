from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import datetime, timedelta
from dateutil import parser

from ..serializers import ShiftSerializer
from ..models import Shift, ShiftAssignment
from ..services.shift_service import ShiftService
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def shift_assignment_calendar_events(request):
    """API endpoint for providing shift assignment events for FullCalendar"""
    start_date_str = request.query_params.get('start')
    end_date_str = request.query_params.get('end')
    department_filter = request.query_params.get('department')
    shift_type_filter = request.query_params.get('shift_type')
    employee_id_filter = request.query_params.get('employee_id')

    try:
        # Parse ISO format dates with timezone
        start_date = parser.parse(start_date_str).date()
        end_date = parser.parse(end_date_str).date()
    except (ValueError, TypeError):
        return Response({'error': 'Invalid date range'}, status=400)

    assignments = ShiftAssignment.objects.filter(
        Q(start_date__lte=end_date) & 
        (Q(end_date__isnull=True) | Q(end_date__gte=start_date)),
        is_active=True
    ).select_related('employee', 'shift', 'employee__department')

    if department_filter:
        assignments = assignments.filter(employee__department_id=department_filter)
    if shift_type_filter:
        assignments = assignments.filter(shift__shift_type=shift_type_filter)
    if employee_id_filter:
        assignments = assignments.filter(employee_id=employee_id_filter)

    events = []
    for assignment in assignments:
        # Get shift timing for this specific date
        shift_timing = ShiftService.get_shift_timing(assignment.shift, assignment.start_date)
        event_title = f"{assignment.employee.get_full_name()} - {assignment.shift.name}"
        timing_str = f"{shift_timing['start_time'].strftime('%I:%M%p')} - {shift_timing['end_time'].strftime('%I:%M%p')}"

        # Create event for each day in the assignment's range
        current_date = max(assignment.start_date, start_date)
        end_date_assignment = assignment.end_date if assignment.end_date else end_date

        while current_date <= min(end_date_assignment, end_date):
            # Get shift timing for this specific date
            daily_timing = ShiftService.get_shift_timing(assignment.shift, current_date)
            events.append({
                'id': assignment.id,
                'title': event_title,
                'start': current_date.isoformat(),
                'end': (current_date + timedelta(days=1)).isoformat(),
                'shift_timing': timing_str,
                'employee_id': assignment.employee.id,
                'shift_id': assignment.shift.id,
                'department': assignment.employee.department.name if assignment.employee.department else None,
                'shift_type': assignment.shift.shift_type,
                'is_date_specific': daily_timing.get('is_date_specific', False),
                'is_ramadan': daily_timing.get('is_ramadan', False),
                'allDay': True,
                'className': [
                    assignment.shift.shift_type.lower(),
                    'date-specific' if daily_timing.get('is_date_specific') else '',
                    'ramadan' if daily_timing.get('is_ramadan') else ''
                ]
            })
            current_date += timedelta(days=1)

    return Response(events)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def quick_shift_assignment(request):
    """API endpoint for quick shift assignments from calendar"""
    try:
        employee_id = request.data.get('employee')
        shift_id = request.data.get('shift')
        date = request.data.get('date')
        start_time = request.data.get('start_time')
        end_time = request.data.get('end_time')

        if not all([employee_id, shift_id, date]):
            return Response({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)

        employee = get_object_or_404(Employee, id=employee_id)
        shift = get_object_or_404(Shift, id=shift_id)

        # Create or update date-specific shift if custom times provided
        if start_time and end_time:
            ShiftService.set_date_specific_shift(
                shift=shift,
                date=datetime.strptime(date, '%Y-%m-%d').date(),
                start_time=datetime.strptime(start_time, '%H:%M').time(),
                end_time=datetime.strptime(end_time, '%H:%M').time(),
                created_by=request.user
            )

        # Create shift assignment
        assignment = ShiftService.assign_shift(
            employee=employee,
            shift=shift,
            start_date=datetime.strptime(date, '%Y-%m-%d').date(),
            end_date=None,  # Quick assignments are for specific dates
            created_by=request.user
        )

        return Response({
            'success': True,
            'assignment_id': assignment.id
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def shift_assignment_detail(request, pk):
    """API endpoint for retrieving, updating, or deleting a shift assignment"""
    assignment = get_object_or_404(ShiftAssignment, pk=pk)

    if request.method == 'GET':
        # Return assignment details
        shift_timing = ShiftService.get_shift_timing(assignment.shift, assignment.start_date)
        return Response({
            'id': assignment.id,
            'employee': {
                'id': assignment.employee.id,
                'name': str(assignment.employee)
            },
            'shift': {
                'id': assignment.shift.id,
                'name': assignment.shift.name,
                'is_night_shift': assignment.shift.shift_type == 'NIGHT'
            },
            'start_date': assignment.start_date,
            'end_date': assignment.end_date,
            'start_time': shift_timing['start_time'],
            'end_time': shift_timing['end_time'],
            'is_date_specific': shift_timing.get('is_date_specific', False)
        })
    
    elif request.method == 'PUT':
        # Update assignment
        try:
            start_time = request.data.get('start_time')
            end_time = request.data.get('end_time')
            
            if start_time and end_time:
                # Update or create date-specific shift timing
                ShiftService.set_date_specific_shift(
                    shift=assignment.shift,
                    date=assignment.start_date,
                    start_time=datetime.strptime(start_time, '%H:%M').time(),
                    end_time=datetime.strptime(end_time, '%H:%M').time(),
                    created_by=request.user
                )
            
            # Update other fields if needed
            if 'end_date' in request.data:
                assignment.end_date = request.data['end_date']
                assignment.save()
            
            return Response({'success': True})
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)
    
    elif request.method == 'DELETE':
        try:
            assignment.delete()
            return Response({'success': True})
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)
