from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'attendance'

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'shifts', views.ShiftViewSet, basename='shift')
router.register(r'records', views.AttendanceRecordViewSet, basename='attendance-record')
router.register(r'logs', views.AttendanceLogViewSet, basename='attendance-log')
router.register(r'leaves', views.LeaveViewSet, basename='leave')
router.register(r'holidays', views.HolidayViewSet, basename='holiday')

# API endpoints
api_urlpatterns = [
    path('calendar-events/', views.get_calendar_events, name='calendar-events'),
    path('employee/<int:employee_id>/attendance/', 
         views.get_employee_attendance, 
         name='employee-attendance'),
]

urlpatterns = [
    # Include API URLs
    path('api/', include((router.urls, 'api'))),
    path('api/', include((api_urlpatterns, 'api'))),
    
    # Template Views
    path('', views.attendance_list, name='attendance_list'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('mark/', views.mark_attendance, name='mark_attendance'),
    path('upload/', views.upload_attendance, name='upload_attendance'),
    
    # Leave Management
    path('leave/', views.leave_request_list, name='leave_request_list'),
    path('leave/create/', views.leave_request_create, name='leave_request_create'),
    path('leave/<int:pk>/', views.leave_request_detail, name='leave_request_detail'),
]
