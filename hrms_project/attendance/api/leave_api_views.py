from datetime import datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.shortcuts import get_object_or_404

from ..models import LeaveType, Employee
from ..services.leave_rule_service import LeaveRuleService

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_leave_request(request):
    """
    Validate a leave request in real-time
    
    Expected payload:
    {
        "employee": "id",  # Optional, only for admin users
        "leave_type": "id",
        "leave_sub_type": "sub_type_code",
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD"
    }
    """
    # Get employee (either from request or specified employee for admin users)
    try:
        if request.user.is_staff and request.data.get('employee'):
            employee = get_object_or_404(Employee, id=request.data.get('employee'))
        else:
            employee = request.user.employee
    except (Employee.DoesNotExist, AttributeError):
        return Response(
            {'message': 'No valid employee found for this request'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get and validate leave type
    leave_type_id = request.data.get('leave_type')
    if not leave_type_id:
        return Response(
            {'message': 'Leave type is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    leave_type = get_object_or_404(LeaveType, id=leave_type_id)
    
    # Get other parameters
    sub_type = request.data.get('leave_sub_type', '')
    
    try:
        start_date = datetime.strptime(
            request.data.get('start_date', ''),
            '%Y-%m-%d'
        ).date()
        end_date = datetime.strptime(
            request.data.get('end_date', ''),
            '%Y-%m-%d'
        ).date()
    except ValueError:
        return Response(
            {'message': 'Invalid date format. Use YYYY-MM-DD'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate the request
    is_valid, message, data = LeaveRuleService.validate_leave_request(
        employee=employee,
        leave_type=leave_type,
        sub_type=sub_type,
        start_date=start_date,
        end_date=end_date
    )
    
    return Response({
        'is_valid': is_valid,
        'message': message,
        'data': data
    }) 