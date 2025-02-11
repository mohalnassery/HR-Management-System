from rest_framework import serializers
from django.contrib.auth import get_user_model
from employees.models import (
    Department, Division, Location, Bank, Employee,
    EmployeeDependent, EmergencyContact, EmployeeDocument,
    EmployeeAsset, EmployeeEducation, EmployeeOffence, LifeEvent
)
from attendance.models import ShiftAssignment, Shift

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class DivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Division
        fields = '__all__'

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    division_name = serializers.CharField(source='division.name', read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='department',
        write_only=True
    )
    division_id = serializers.PrimaryKeyRelatedField(
        queryset=Division.objects.all(),
        source='division',
        write_only=True
    )

    class Meta:
        model = Employee
        fields = '__all__'

class EmployeeDependentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDependent
        fields = '__all__'

class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = '__all__'

class EmployeeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDocument
        fields = '__all__'

class EmployeeAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeAsset
        fields = '__all__'

class EmployeeEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeEducation
        fields = '__all__'

class EmployeeOffenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeOffence
        fields = '__all__'

class LifeEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = LifeEvent
        fields = '__all__'

class ShiftOverlapSerializer(serializers.ModelSerializer):
    shift_name = serializers.CharField(source='shift.name')
    start_time = serializers.TimeField(source='shift.start_time')
    end_time = serializers.TimeField(source='shift.end_time')
    is_night_shift = serializers.BooleanField(source='shift.is_night_shift')

    class Meta:
        model = ShiftAssignment
        fields = ('id', 'shift_name', 'start_date', 'end_date', 'start_time', 'end_time', 'is_night_shift')
