from rest_framework import serializers
from typing import Optional, Any
from django.contrib.auth import get_user_model
from .models import (
    Shift, AttendanceRecord, AttendanceLog,
    AttendanceEdit, Leave, Holiday
)
from employees.models import Employee

User = get_user_model()

class EmployeeNameMixin:
    """
    Mixin that provides employee name serialization functionality.
    Requires the model to have an 'employee' field.
    """
    employee_name = serializers.SerializerMethodField()

    def get_employee_name(self, obj: Any) -> Optional[str]:
        """Get employee's full name"""
        if hasattr(obj, 'employee') and obj.employee:
            return obj.employee.get_full_name()
        return None

class UserNameMixin:
    """
    Mixin that provides user name serialization functionality.
    Used for fields like created_by, edited_by, approved_by.
    """
    def get_user_name(self, user: Optional[User]) -> Optional[str]:
        """Get user's full name if user exists"""
        return user.get_full_name() if user else None

    def get_created_by_name(self, obj: Any) -> Optional[str]:
        """Get creating user's full name"""
        return self.get_user_name(getattr(obj, 'created_by', None))

    def get_edited_by_name(self, obj: Any) -> Optional[str]:
        """Get editing user's full name"""
        return self.get_user_name(getattr(obj, 'edited_by', None))

    def get_approved_by_name(self, obj: Any) -> Optional[str]:
        """Get approving user's full name"""
        return self.get_user_name(getattr(obj, 'approved_by', None))

class StatusDeterminationMixin:
    """
    Mixin that provides status determination functionality.
    Can be extended for different status determination needs.
    """
    def determine_status(self, obj: Any, check_leave: bool = True, check_holiday: bool = True) -> Optional[str]:
        """
        Determine status based on various conditions.
        
        Args:
            obj: The object to determine status for
            check_leave: Whether to check for leave status
            check_holiday: Whether to check for holiday status
            
        Returns:
            Status string or None
        """
        if check_leave:
            # Check for approved leave
            is_on_leave = Leave.objects.filter(
                employee=obj.employee,
                start_date__lte=obj.date,
                end_date__gte=obj.date,
                status='approved'
            ).exists()
            
            if is_on_leave:
                return 'leave'

        if check_holiday:
            # Check if the date is a holiday
            is_holiday = Holiday.objects.filter(
                date=obj.date,
                is_active=True
            ).exists()
            
            if is_holiday:
                if hasattr(obj, 'first_in_time') and obj.first_in_time:
                    return 'present'
                return None

        # Normal day status logic
        if hasattr(obj, 'is_late') and obj.is_late:
            return 'late'
        elif hasattr(obj, 'first_in_time') and obj.first_in_time:
            return 'present'
        return 'absent'

class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'

class AttendanceRecordSerializer(serializers.ModelSerializer, EmployeeNameMixin):
    class Meta:
        model = AttendanceRecord
        fields = '__all__'

class AttendanceLogSerializer(serializers.ModelSerializer, EmployeeNameMixin, StatusDeterminationMixin):
    shift_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()
    personnel_id = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceLog
        fields = '__all__'

    def get_shift_name(self, obj: AttendanceLog) -> Optional[str]:
        return obj.shift.name if obj.shift else None

    def get_employee_id(self, obj: AttendanceLog) -> Optional[int]:
        return obj.employee.id if obj.employee else None

    def get_personnel_id(self, obj: AttendanceLog) -> Optional[str]:
        return obj.employee.employee_number if obj.employee else None
        
    def get_status(self, obj: AttendanceLog) -> Optional[str]:
        return self.determine_status(obj)

class AttendanceEditSerializer(serializers.ModelSerializer, UserNameMixin):
    edited_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceEdit
        fields = '__all__'

class LeaveSerializer(serializers.ModelSerializer, EmployeeNameMixin, UserNameMixin):
    approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Leave
        fields = '__all__'

class HolidaySerializer(serializers.ModelSerializer, UserNameMixin):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Holiday
        fields = '__all__'

class AttendanceUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

class BulkAttendanceCreateSerializer(serializers.Serializer):
    records = serializers.ListField(
        child=serializers.DictField()
    )

    def validate(self, data: dict) -> dict:
        records = data.get('records', [])
        for record in records:
            if not all(k in record for k in ('employee_id', 'timestamp')):
                raise serializers.ValidationError(
                    "Each record must contain employee_id and timestamp"
                )
        return data

    def create(self, validated_data: dict) -> list:
        records = validated_data.get('records', [])
        created_records = []

        for record in records:
            try:
                employee = Employee.objects.get(id=record['employee_id'])
                attendance_record = AttendanceRecord.objects.create(
                    employee=employee,
                    timestamp=record['timestamp'],
                    device_name=record.get('device_name', ''),
                    event_point=record.get('event_point', ''),
                    verify_type=record.get('verify_type', ''),
                    event_description=record.get('event_description', ''),
                    remarks=record.get('remarks', '')
                )
                created_records.append(attendance_record)
            except Employee.DoesNotExist:
                continue

        return created_records