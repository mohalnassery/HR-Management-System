from rest_framework import serializers
from .models import (
    Shift, AttendanceRecord, AttendanceLog,
    AttendanceEdit, Leave, Holiday
)
from employees.models import Employee

class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'

class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceRecord
        fields = '__all__'

    def get_employee_name(self, obj):
        return obj.employee.get_full_name()

class AttendanceLogSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    shift_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()
    personnel_id = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceLog
        fields = '__all__'

    def get_employee_name(self, obj):
        return obj.employee.get_full_name() if obj.employee else None

    def get_shift_name(self, obj):
        return obj.shift.name if obj.shift else None

    def get_employee_id(self, obj):
        return obj.employee.id if obj.employee else None

    def get_personnel_id(self, obj):
        return obj.employee.employee_number if obj.employee else None

class AttendanceEditSerializer(serializers.ModelSerializer):
    edited_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceEdit
        fields = '__all__'

    def get_edited_by_name(self, obj):
        return obj.edited_by.get_full_name() if obj.edited_by else None

class LeaveSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Leave
        fields = '__all__'

    def get_employee_name(self, obj):
        return obj.employee.get_full_name()

    def get_approved_by_name(self, obj):
        return obj.approved_by.get_full_name() if obj.approved_by else None

class HolidaySerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Holiday
        fields = '__all__'

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

class AttendanceUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

class BulkAttendanceCreateSerializer(serializers.Serializer):
    records = serializers.ListField(
        child=serializers.DictField()
    )

    def validate(self, data):
        records = data.get('records', [])
        for record in records:
            if not all(k in record for k in ('employee_id', 'timestamp')):
                raise serializers.ValidationError(
                    "Each record must contain employee_id and timestamp"
                )
        return data

    def create(self, validated_data):
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