from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import ShiftAssignment
from datetime import datetime
import dateutil.parser

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def shift_assignments(request):
    """API endpoint for FullCalendar to fetch shift assignments"""
    # Get query parameters
    start = request.GET.get('start')
    end = request.GET.get('end')
    department = request.GET.get('department')
    shift_type = request.GET.get('shift_type')
    employee = request.GET.get('employee')

    # Base queryset
    queryset = ShiftAssignment.objects.filter(is_active=True).select_related('employee', 'shift')

    # Apply filters
    if start:
        try:
            start_date = dateutil.parser.parse(start).date()
            queryset = queryset.filter(start_date__gte=start_date)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid start date format'}, status=400)
            
    if end:
        try:
            end_date = dateutil.parser.parse(end).date()
            queryset = queryset.filter(
                start_date__lte=end_date
            ).exclude(
                end_date__lt=start_date
            )
        except (ValueError, TypeError):
            return Response({'error': 'Invalid end date format'}, status=400)
    if department:
        queryset = queryset.filter(employee__department_id=department)
    if shift_type:
        queryset = queryset.filter(shift__shift_type=shift_type)
    if employee:
        queryset = queryset.filter(employee_id=employee)

    # Convert to FullCalendar events format
    events = []
    for assignment in queryset:
        event = {
            'id': assignment.id,
            'title': f"{assignment.employee.get_full_name()} - {assignment.shift.name}",
            'start': assignment.start_date.isoformat(),
            'end': assignment.end_date.isoformat() if assignment.end_date else None,
            'allDay': True,
            'extendedProps': {
                'employee_id': assignment.employee.id,
                'shift_id': assignment.shift.id,
                'shift_type': assignment.shift.shift_type,
                'is_date_specific': assignment.end_date is not None,
                'is_ramadan': False  # TODO: Add Ramadan check logic
            }
        }
        events.append(event)

    return Response(events)
