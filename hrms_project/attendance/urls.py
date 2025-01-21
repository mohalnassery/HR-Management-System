from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'attendance'

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'shifts', views.ShiftViewSet, basename='shift')
router.register(r'records', views.AttendanceRecordViewSet, basename='attendance-record')
router.register(r'logs', views.AttendanceLogViewSet, basename='attendance-log')
router.register(r'leaves', views.LeaveViewSet, basename='leave')
router.register(r'holidays', views.HolidayViewSet, basename='holiday')

urlpatterns = [
    # API Endpoints
    path('api/', include(router.urls)),
    path('api/employee/<int:employee_id>/attendance/', 
         views.get_employee_attendance, 
         name='employee-attendance'),
    
    # Template Views
    path('', views.attendance_list, name='attendance_list'),
    path('mark/', views.mark_attendance, name='mark_attendance'),
    
    # Leave Management
    path('leave/', views.leave_request_list, name='leave_request_list'),
    path('leave/create/', views.leave_request_create, name='leave_request_create'),
    path('leave/<int:pk>/', views.leave_request_detail, name='leave_request_detail'),
]

# API URL patterns will include:
# /api/shifts/ - List and create shifts
# /api/shifts/{id}/ - Retrieve, update, delete shift
# /api/records/ - List and create attendance records
# /api/records/upload_excel/ - Upload attendance Excel file
# /api/logs/ - List and create attendance logs
# /api/logs/{id}/edit_attendance/ - Edit attendance
# /api/leaves/ - List and create leave requests
# /api/leaves/{id}/approve_leave/ - Approve/reject leave
# /api/holidays/ - List and create holidays
# /api/employee/{id}/attendance/ - Get employee attendance summary
