from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'attendance'

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'shifts', views.ShiftViewSet, basename='shift')
router.register(r'records', views.AttendanceRecordViewSet, basename='attendance-record')
router.register(r'logs', views.AttendanceLogListViewSet, basename='attendance-log')
router.register(r'leaves', views.LeaveViewSet, basename='leave')
router.register(r'holidays', views.HolidayViewSet, basename='holiday')
router.register(r'attendance-logs', views.AttendanceLogListViewSet, basename='attendance-log-list')

urlpatterns = [
    # Template views
    path('', views.attendance_list, name='attendance_list'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/month/', views.calendar_month, name='calendar_month'),
    path('calendar/week/', views.calendar_week, name='calendar_week'),
    path('calendar/department/', views.calendar_department, name='calendar_department'),
    path('mark/', views.mark_attendance, name='mark_attendance'),
    path('upload/', views.upload_attendance, name='upload_attendance'),
    path('report/', views.attendance_report, name='attendance_report'),
    path('detail/<int:log_id>/', views.attendance_detail_view, name='attendance_detail'),
    path('leaves/', views.leave_request_list, name='leave_request_list'),
    path('leaves/create/', views.leave_request_create, name='leave_request_create'),
    path('leaves/<int:pk>/', views.leave_request_detail, name='leave_request_detail'),
    path('leaves/balance/', views.leave_balance, name='leave_balance'),
    path('leaves/types/', views.leave_types, name='leave_types'),
    
    # Holiday management
    path('holidays/', views.holiday_list, name='holiday_list'),
    path('holidays/create/', views.holiday_create, name='holiday_create'),
    path('holidays/recurring/', views.recurring_holidays, name='recurring_holidays'),

    # API endpoints
    path('api/', include(router.urls)),
    path('api/logs/<int:log_id>/details/', views.attendance_detail_api, name='attendance-detail-api'),
    path('api/search-employees/', views.search_employees, name='search_employees'),
    path('api/calendar-events/', views.calendar_events, name='calendar_events'),
    path('api/attendance-details/<int:log_id>/', views.attendance_details, name='attendance_details'),
    path('api/employee/<int:employee_id>/attendance/', views.get_employee_attendance, name='employee-attendance'),
    path('api/records/<int:record_id>/', views.attendance_record_api, name='attendance-record-api'),
    path('api/records/', views.add_attendance_record, name='add-attendance-record'),
    path('api/get-department-employees/', views.get_department_employees, name='get_department_employees'),
]
