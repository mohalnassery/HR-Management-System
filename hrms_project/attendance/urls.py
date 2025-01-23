from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'attendance'

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'shifts', views.ShiftViewSet, basename='shift')
router.register(r'records', views.AttendanceRecordViewSet, basename='attendance-record')
router.register(r'logs', views.AttendanceLogListViewSet, basename='attendance-log')

urlpatterns = [
    # Main views
    path('', views.attendance_list, name='attendance_list'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('mark/', views.mark_attendance, name='mark_attendance'),
    path('upload/', views.upload_attendance, name='upload_attendance'),
    path('detail/<int:log_id>/', views.attendance_detail_view, name='attendance_detail'),
    
    # API endpoints
    path('api/', include(router.urls)),
    path('api/logs/<int:log_id>/details/', views.attendance_detail_api, name='attendance-detail-api'),
    path('api/calendar-events/', views.get_calendar_events, name='calendar-events'),
    path('api/employee/<int:employee_id>/attendance/', views.get_employee_attendance, name='employee-attendance'),
    path('api/records/<int:record_id>/', views.attendance_record_api, name='attendance-record-api'),
    path('api/records/', views.add_attendance_record, name='add-attendance-record'),
]
