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
from django.views.decorators.http import require_http_methods
from django.utils.dateparse import parse_date
from calendar import monthrange
from django.db import transaction
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Module-level flag to track if we've already logged the cache import message
_cache_import_logged = False

# Try to import cache, but don't fail if it's not configured
try:
    from django.core.cache import cache
    # Only log once
    if not _cache_import_logged:
        logger.info("Successfully imported cache")
        _cache_import_logged = True
except ImportError:
    if not _cache_import_logged:
        logger.warning("Failed to import cache, continuing without caching")
        _cache_import_logged = True
    cache = None

from ..serializers import ShiftSerializer
from ..models import Shift, ShiftAssignment, DateSpecificShiftOverride
from ..services.shift_service import ShiftService
from employees.models import Employee, Department

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
    # Get filter parameters
    department_id = request.GET.get('department')
    shift_id = request.GET.get('shift')
    status = request.GET.get('status')
    assignment_type = request.GET.get('type')
    search_query = request.GET.get('search')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Start with all assignments
    assignments = ShiftAssignment.objects.select_related(
        'employee', 
        'employee__department', 
        'shift', 
        'created_by'
    ).order_by('-created_at')

    # Apply filters
    if department_id:
        assignments = assignments.filter(employee__department_id=department_id)
    if shift_id:
        assignments = assignments.filter(shift_id=shift_id)
    if status:
        if status == 'active':
            assignments = assignments.filter(is_active=True)
        elif status == 'inactive':
            assignments = assignments.filter(is_active=False)
    if assignment_type:
        if assignment_type == 'permanent':
            assignments = assignments.filter(end_date__isnull=True)
        elif assignment_type == 'temporary':
            assignments = assignments.filter(end_date__isnull=False)
    if search_query:
        assignments = assignments.filter(
            Q(employee__first_name__icontains=search_query) |
            Q(employee__last_name__icontains=search_query) |
            Q(employee__employee_number__icontains=search_query)
        )
    if start_date:
        assignments = assignments.filter(start_date__gte=start_date)
    if end_date:
        assignments = assignments.filter(
            Q(end_date__lte=end_date) | 
            Q(end_date__isnull=True, start_date__lte=end_date)
        )

    # Paginate results
    paginator = Paginator(assignments, 10)  # Show 10 assignments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'shifts': Shift.objects.all(),
        'departments': Department.objects.all(),
        'employees': Employee.objects.select_related('department').all(),
        # Add filter values to context for maintaining state
        'selected_department': department_id,
        'selected_shift': shift_id,
        'selected_status': status,
        'selected_type': assignment_type,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'attendance/shifts/assignment_list.html', context)

@login_required
def shift_assignment_create(request):
    """View for creating a new shift assignment"""
    if request.method == 'POST':
        # Get comma-separated employee IDs and split them
        employee_ids = request.POST.getlist('employee[]', [])
        logger.debug(f"Received employee_ids: {employee_ids}")
        
        if not employee_ids:  # Check if the list is empty
            messages.error(request, 'Please select at least one employee.')
            return redirect('attendance:shift_assignment_create')

        shift_id = request.POST.get('shift')
        if not shift_id:
            messages.error(request, 'Please select a shift.')
            return redirect('attendance:shift_assignment_create')

        start_date = request.POST.get('start_date')
        if not start_date:
            messages.error(request, 'Please provide a start date.')
            return redirect('attendance:shift_assignment_create')

        end_date = request.POST.get('end_date') or None
        is_active = request.POST.get('is_active') == 'on'
        
        logger.info(f"Creating shift assignments - Shift: {shift_id}, Start: {start_date}, End: {end_date}, Active: {is_active}")

        try:
            with transaction.atomic():
                created_count = 0
                for employee_id in employee_ids:
                    # Skip empty employee IDs
                    if not employee_id:
                        logger.warning(f"Skipping empty employee_id")
                        continue

                    # Validate employee exists
                    try:
                        employee = Employee.objects.get(id=employee_id)
                        logger.debug(f"Found employee: {employee.get_full_name()}")
                    except Employee.DoesNotExist:
                        logger.error(f"Employee with ID {employee_id} does not exist")
                        messages.error(request, f'Employee with ID {employee_id} does not exist.')
                        continue

                    # Deactivate any existing active assignments for this employee
                    deactivated = ShiftAssignment.objects.filter(
                        employee_id=employee_id,
                        is_active=True
                    ).update(is_active=False)
                    logger.debug(f"Deactivated {deactivated} existing assignments for employee {employee_id}")

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
                    logger.debug(f"Created new assignment for employee {employee_id}")

                if created_count > 0:
                    success_msg = f'{created_count} Shift assignment{"s" if created_count > 1 else ""} created successfully.'
                    logger.info(success_msg)
                    messages.success(request, success_msg)
                    
                    # Clear any cached shift assignments
                    for employee_id in employee_ids:
                        if employee_id:
                            cache_key = f'employee_shifts_{employee_id}'
                            logger.debug(f"Attempting to clear cache for key: {cache_key}")
                            if cache:
                                try:
                                    cache.delete(cache_key)
                                    logger.debug(f"Successfully cleared cache for key: {cache_key}")
                                except Exception as cache_error:
                                    logger.error(f"Error clearing cache for key {cache_key}: {str(cache_error)}")
                    
                    return redirect('attendance:shift_assignment_list')
                else:
                    warning_msg = 'No shift assignments were created. Please check your selections.'
                    logger.warning(warning_msg)
                    messages.warning(request, warning_msg)

        except Exception as e:
            error_msg = f'Error assigning shift: {str(e)}'
            logger.error(error_msg, exc_info=True)
            messages.error(request, error_msg)

    # Get active employees and shifts
    employees = Employee.objects.filter(is_active=True).select_related('department')
    shifts = Shift.objects.filter(is_active=True)
    departments = Department.objects.all()

    return render(request, 'attendance/shifts/assignment_form.html', {
        'employees': employees,
        'shifts': shifts,
        'departments': departments
    })

@login_required
def shift_assignment_edit(request, pk):
    """View for editing a shift assignment"""
    assignment = get_object_or_404(ShiftAssignment.objects.select_related(
        'employee', 
        'employee__department', 
        'shift'
    ), pk=pk)

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
    departments = Department.objects.all()

    context = {
        'form': assignment,  # Pass the assignment as form for template
        'employees': employees,
        'shifts': shifts,
        'departments': departments,
        'title': 'Edit Shift Assignment'  # Add a title for the page
    }

    return render(request, 'attendance/shifts/assignment_form.html', context)

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
    view_type = request.query_params.get('view', 'dayGridMonth')

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
        current_date = max(assignment.start_date, start_date)
        end_date_assignment = assignment.end_date if assignment.end_date else end_date

        while current_date <= min(end_date_assignment, end_date):
            # Get shift timing for this specific date
            daily_timing = ShiftService.get_shift_timing(assignment.shift, current_date)
            
            # Check for night shift override
            night_shift_override = None
            if assignment.shift.is_night_shift:
                night_shift_override = DateSpecificShiftOverride.objects.filter(
                    date=current_date,
                    shift_type='NIGHT'
                ).first()

            # Set event start and end times based on view type
            if view_type in ['timeGridWeek', 'timeGridDay']:
                if assignment.shift.is_night_shift:
                    # For night shifts in week/day view, create event spanning to next day
                    if night_shift_override:
                        start_time = night_shift_override.override_start_time
                        end_time = night_shift_override.override_end_time
                    else:
                        start_time = daily_timing['start_time']
                        end_time = daily_timing['end_time']
                    
                    # Create event spanning to next day
                    next_day = current_date + timedelta(days=1)
                    event_start = datetime.combine(current_date, start_time)
                    event_end = datetime.combine(next_day, end_time)
                else:
                    # For regular shifts, keep within same day
                    event_start = datetime.combine(current_date, daily_timing['start_time'])
                    event_end = datetime.combine(current_date, daily_timing['end_time'])
            else:
                # For month view, use all-day events
                event_start = current_date
                event_end = current_date + timedelta(days=1)

            # Format the timing string for display
            if night_shift_override:
                timing_str = f"{night_shift_override.override_start_time.strftime('%I:%M %p')} - {night_shift_override.override_end_time.strftime('%I:%M %p')}"
            else:
                timing_str = f"{daily_timing['start_time'].strftime('%I:%M %p')} - {daily_timing['end_time'].strftime('%I:%M %p')}"

            # Set event properties
            event = {
                'id': f"{assignment.id}_{current_date.isoformat()}",
                'title': f"{assignment.employee.get_full_name()} - {assignment.shift.name}",
                'start': event_start.isoformat() if isinstance(event_start, datetime) else event_start.isoformat(),
                'end': event_end.isoformat() if isinstance(event_end, datetime) else event_end.isoformat(),
                'shift_timing': timing_str,
                'employee_id': assignment.employee.id,
                'shift_id': assignment.shift.id,
                'department': assignment.employee.department.name if assignment.employee.department else None,
                'shift_type': assignment.shift.shift_type,
                'is_date_specific': daily_timing.get('is_date_specific', False) or bool(night_shift_override),
                'is_ramadan': daily_timing.get('is_ramadan', False),
                'allDay': view_type == 'dayGridMonth',
                'className': [
                    f'shift-type-{assignment.shift.shift_type.lower()}',
                    'date-specific' if daily_timing.get('is_date_specific') or bool(night_shift_override) else '',
                    'ramadan' if daily_timing.get('is_ramadan', False) else ''
                ]
            }
            events.append(event)
            current_date += timedelta(days=1)

    return Response(events)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def quick_shift_assignment(request):
    """API endpoint for quick shift assignments from calendar"""
    try:
        # Get employee IDs from the array format
        employee_ids = request.data.get('employee[]', '').split(',')
        shift_id = request.data.get('shift')
        date = request.data.get('date')
        start_time = request.data.get('start_time')
        end_time = request.data.get('end_time')

        if not all([employee_ids, shift_id, date]) or not employee_ids[0]:
            return Response({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)

        shift = get_object_or_404(Shift, id=shift_id)
        assignments = []
        skipped = []
        
        # Parse the date once
        assignment_date = datetime.strptime(date, '%Y-%m-%d').date()

        # Check for night shift override if this is a night shift
        if shift.shift_type == 'NIGHT':
            override = DateSpecificShiftOverride.objects.filter(
                date=assignment_date,
                shift_type='NIGHT'
            ).first()
            
            if override:
                # Use override times instead of custom times for night shift
                start_time = override.override_start_time.strftime('%H:%M')
                end_time = override.override_end_time.strftime('%H:%M')

        # Create or update date-specific shift if custom times provided
        if start_time and end_time and shift.shift_type != 'NIGHT':
            ShiftService.set_date_specific_shift(
                shift=shift,
                date=assignment_date,
                start_time=datetime.strptime(start_time, '%H:%M').time(),
                end_time=datetime.strptime(end_time, '%H:%M').time(),
                created_by=request.user
            )

        # Create assignments for all selected employees
        for employee_id in employee_ids:
            try:
                employee = get_object_or_404(Employee, id=employee_id)
                
                # Check for existing assignments on this date
                existing_assignments = ShiftAssignment.objects.filter(
                    employee=employee,
                    start_date__lte=assignment_date,
                    end_date__gte=assignment_date,
                    is_active=True
                ).select_related('shift')

                if existing_assignments.exists():
                    # Get the highest priority existing assignment
                    highest_priority_assignment = max(
                        existing_assignments,
                        key=lambda x: x.shift.priority
                    )

                    # Skip if existing assignment has higher or equal priority
                    if highest_priority_assignment.shift.priority >= shift.priority:
                        skipped.append({
                            'employee': str(employee),
                            'reason': f'Already assigned to {highest_priority_assignment.shift.name} (higher priority)'
                        })
                        continue
                    else:
                        # Deactivate lower priority assignments for this date
                        for existing in existing_assignments:
                            if existing.start_date == existing.end_date == assignment_date:
                                # If it's a single-day assignment, deactivate it
                                existing.is_active = False
                                existing.save()
                            else:
                                # If it's a multi-day assignment, split it
                                if existing.start_date < assignment_date:
                                    # Create a new assignment for the days before
                                    ShiftAssignment.objects.create(
                                        employee=employee,
                                        shift=existing.shift,
                                        start_date=existing.start_date,
                                        end_date=assignment_date - timedelta(days=1),
                                        is_active=True,
                                        created_by=request.user
                                    )
                                if existing.end_date > assignment_date:
                                    # Create a new assignment for the days after
                                    ShiftAssignment.objects.create(
                                        employee=employee,
                                        shift=existing.shift,
                                        start_date=assignment_date + timedelta(days=1),
                                        end_date=existing.end_date,
                                        is_active=True,
                                        created_by=request.user
                                    )
                                # Deactivate the original assignment
                                existing.is_active = False
                                existing.save()

                # Create new assignment
                assignment = ShiftService.assign_shift(
                    employee=employee,
                    shift=shift,
                    start_date=assignment_date,
                    end_date=assignment_date,  # Set end_date to the same as start_date
                    created_by=request.user
                )
                assignments.append(assignment.id)
            except Exception as e:
                print(f"Error assigning shift to employee {employee_id}: {str(e)}")
                skipped.append({
                    'employee': str(employee),
                    'reason': str(e)
                })
                continue

        if assignments:
            response_data = {
                'success': True,
                'assignment_ids': assignments,
                'message': f'Successfully assigned shift to {len(assignments)} employees for {date}'
            }
            if skipped:
                response_data['skipped'] = skipped
            return Response(response_data)
        else:
            return Response({
                'success': False,
                'error': 'No assignments were created',
                'skipped': skipped
            }, status=400)

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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_shift_override(request):
    """Create or update a night shift override for a specific date"""
    try:
        date = parse_date(request.POST.get('date'))
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        if not all([date, start_time, end_time]):
            return Response({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)

        # Convert time strings to time objects
        start_time = datetime.strptime(start_time, '%H:%M').time()
        end_time = datetime.strptime(end_time, '%H:%M').time()

        # Create or update override
        override, created = DateSpecificShiftOverride.objects.update_or_create(
            date=date,
            shift_type='NIGHT',
            defaults={
                'override_start_time': start_time,
                'override_end_time': end_time
            }
        )

        return Response({
            'success': True,
            'override_id': override.id,
            'created': created
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_shift_override(request, date):
    """Remove a night shift override for a specific date"""
    try:
        date = parse_date(date)
        if not date:
            return Response({
                'success': False,
                'error': 'Invalid date format'
            }, status=400)

        # Delete the override if it exists
        override = DateSpecificShiftOverride.objects.filter(
            date=date,
            shift_type='NIGHT'
        ).first()

        if override:
            override.delete()
            return Response({'success': True})
        else:
            return Response({
                'success': False,
                'error': 'Override not found'
            }, status=404)

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_shift_overrides(request, year, month):
    """Get all night shift overrides for a specific month"""
    try:
        # Validate year and month
        year = int(year)
        month = int(month)
        if not (1 <= month <= 12):
            raise ValueError('Invalid month')

        # Get the first and last day of the month
        _, last_day = monthrange(year, month)
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, last_day).date()

        # Get all overrides for the month
        overrides = DateSpecificShiftOverride.objects.filter(
            date__range=(start_date, end_date),
            shift_type='NIGHT'
        )

        # Format the response
        override_dict = {
            override.date.isoformat(): {
                'start_time': override.override_start_time.strftime('%H:%M'),
                'end_time': override.override_end_time.strftime('%H:%M')
            }
            for override in overrides
        }

        return Response(override_dict)

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
def shift_day_detail(request, date):
    """View for showing all shifts and their assigned employees for a specific day"""
    try:
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Invalid date format')
        return redirect('attendance:shift_assignment_list')

    # Get all shifts
    shifts = Shift.objects.filter(is_active=True)
    
    # Get night shift override for this date if exists
    night_shift_override = DateSpecificShiftOverride.objects.filter(
        date=selected_date,
        shift_type='NIGHT'
    ).first()
    
    # Get all assignments for this day
    assignments = ShiftAssignment.objects.filter(
        Q(start_date__lte=selected_date) & 
        (Q(end_date__isnull=True) | Q(end_date__gte=selected_date)),
        is_active=True
    ).select_related('employee', 'shift', 'employee__department')

    # Group assignments by shift type
    shift_groups = {
        'DEFAULT': {'name': 'Default Shift (7AM-4PM)', 'assignments': []},
        'NIGHT': {
            'name': 'Night Shift',
            'timing': f"{night_shift_override.override_start_time.strftime('%I:%M %p')} - {night_shift_override.override_end_time.strftime('%I:%M %p')}" if night_shift_override else '6PM-3AM',
            'is_overridden': bool(night_shift_override),
            'assignments': []
        },
        'OPEN': {'name': 'Open Shift', 'assignments': []}
    }

    for assignment in assignments:
        shift_type = assignment.shift.shift_type
        if shift_type in shift_groups:
            # Get shift timing for this specific date
            if shift_type == 'NIGHT' and night_shift_override:
                timing = f"{night_shift_override.override_start_time.strftime('%I:%M %p')} - {night_shift_override.override_end_time.strftime('%I:%M %p')}"
                is_date_specific = True
                is_ramadan = False  # Override takes precedence over Ramadan timing
            else:
                shift_timing = ShiftService.get_shift_timing(assignment.shift, selected_date)
                timing = f"{shift_timing['start_time'].strftime('%I:%M %p')} - {shift_timing['end_time'].strftime('%I:%M %p')}"
                is_date_specific = shift_timing.get('is_date_specific', False)
                is_ramadan = shift_timing.get('is_ramadan', False)
            
            shift_groups[shift_type]['assignments'].append({
                'employee': assignment.employee,
                'shift': assignment.shift,
                'timing': timing,
                'is_date_specific': is_date_specific,
                'is_ramadan': is_ramadan
            })

    # Get all active employees for the quick assignment modal
    employees = Employee.objects.filter(
        is_active=True
    ).select_related('department').order_by('department__name', 'first_name')

    context = {
        'date': selected_date,
        'shift_groups': shift_groups,
        'departments': Department.objects.all(),
        'shifts': shifts,
        'employees': employees,
        'night_shift_override': night_shift_override,
    }
    
    return render(request, 'attendance/shifts/day_detail.html', context)
