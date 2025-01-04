from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .serializers import (
    DepartmentSerializer, DivisionSerializer, LocationSerializer,
    BankSerializer, EmployeeSerializer, EmployeeDependentSerializer,
    EmergencyContactSerializer, EmployeeDocumentSerializer,
    EmployeeAssetSerializer, EmployeeEducationSerializer,
    EmployeeOffenceSerializer, LifeEventSerializer
)
from employees.models import (
    Department, Division, Location, Bank, Employee,
    EmployeeDependent, EmergencyContact, EmployeeDocument,
    EmployeeAsset, EmployeeEducation, EmployeeOffence, LifeEvent
)

User = get_user_model()

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

class DivisionViewSet(viewsets.ModelViewSet):
    queryset = Division.objects.all()
    serializer_class = DivisionSerializer
    permission_classes = [IsAuthenticated]

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]

class BankViewSet(viewsets.ModelViewSet):
    queryset = Bank.objects.all()
    serializer_class = BankSerializer
    permission_classes = [IsAuthenticated]

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Employee.objects.all()
        department = self.request.query_params.get('department', None)
        if department is not None:
            queryset = queryset.filter(department=department)
        return queryset

class EmployeeDependentViewSet(viewsets.ModelViewSet):
    queryset = EmployeeDependent.objects.all()
    serializer_class = EmployeeDependentSerializer
    permission_classes = [IsAuthenticated]

class EmergencyContactViewSet(viewsets.ModelViewSet):
    queryset = EmergencyContact.objects.all()
    serializer_class = EmergencyContactSerializer
    permission_classes = [IsAuthenticated]

class EmployeeDocumentViewSet(viewsets.ModelViewSet):
    queryset = EmployeeDocument.objects.all()
    serializer_class = EmployeeDocumentSerializer
    permission_classes = [IsAuthenticated]

class EmployeeAssetViewSet(viewsets.ModelViewSet):
    queryset = EmployeeAsset.objects.all()
    serializer_class = EmployeeAssetSerializer
    permission_classes = [IsAuthenticated]

class EmployeeEducationViewSet(viewsets.ModelViewSet):
    queryset = EmployeeEducation.objects.all()
    serializer_class = EmployeeEducationSerializer
    permission_classes = [IsAuthenticated]

class EmployeeOffenceViewSet(viewsets.ModelViewSet):
    queryset = EmployeeOffence.objects.all()
    serializer_class = EmployeeOffenceSerializer
    permission_classes = [IsAuthenticated]

class LifeEventViewSet(viewsets.ModelViewSet):
    queryset = LifeEvent.objects.all()
    serializer_class = LifeEventSerializer
    permission_classes = [IsAuthenticated]
