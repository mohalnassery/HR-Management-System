from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet)
router.register(r'divisions', views.DivisionViewSet)
router.register(r'locations', views.LocationViewSet)
router.register(r'banks', views.BankViewSet)
router.register(r'employees', views.EmployeeViewSet)
router.register(r'dependents', views.EmployeeDependentViewSet)
router.register(r'emergency-contacts', views.EmergencyContactViewSet)
router.register(r'documents', views.EmployeeDocumentViewSet)
router.register(r'assets', views.EmployeeAssetViewSet)
router.register(r'education', views.EmployeeEducationViewSet)
router.register(r'offences', views.EmployeeOffenceViewSet)
router.register(r'life-events', views.LifeEventViewSet)

app_name = 'api'

urlpatterns = [
    path('v1/', include(router.urls)),
    path('v1/auth/', include('rest_framework.urls')),
]
