from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'attendance'

# Create a router and register the ShiftViewSet
router = DefaultRouter()
router.register(r'api/shifts', views.ShiftViewSet, basename='shift')

urlpatterns = [
    # Existing URLs
    path('attendance_list/', views.attendance_list, name='attendance_list'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/month/', views.calendar_month, name='calendar_month'),
    path('calendar/week/', views.calendar_week, name='calendar_week'),
    path('calendar/department/', views.calendar_department, name='calendar_department'),
    path('mark_attendance/', views.mark_attendance, name='mark_attendance'),
    path('leave_request_list/', views.leave_request_list, name='leave_request_list'),
    path('detail/', views.attendance_detail_view, name='attendance_detail'),

    path('leave_request_create/', views.leave_request_create, name='leave_request_create'),
    path('leave_request_detail/<int:pk>/', views.leave_request_detail, name='leave_request_detail'),
    path('upload_attendance/', views.upload_attendance, name='upload_attendance'),
    path('attendance_report/', views.attendance_report, name='attendance_report'),
    path('holiday_list/', views.holiday_list, name='holiday_list'),
    path('holiday_create/', views.holiday_create, name='holiday_create'),
    path('recurring_holidays/', views.recurring_holidays, name='recurring_holidays'),
    path('leave_balance/', views.leave_balance, name='leave_balance'),
    path('leave_types/', views.leave_types, name='leave_types'),
    path('get_department_employees/', views.get_department_employees, name='get_department_employees'),
    
    # API endpoints
    path('api/get_calendar_events/', views.get_calendar_events, name='get_calendar_events'),
    path('api/get_employee_attendance/<int:employee_id>/', views.get_employee_attendance, name='get_employee_attendance'),
    path('api/attendance_detail/', views.attendance_detail_api, name='attendance_detail_api'),
    path('api/attendance_record/<int:record_id>/', views.attendance_record_api, name='attendance_record_api'),
    path('api/add_attendance_record/', views.add_attendance_record, name='add_attendance_record'),
    path('api/search_employees/', views.search_employees, name='search_employees'),
    path('api/calendar_events/', views.calendar_events, name='calendar_events'),
    path('api/attendance_details/', views.attendance_details, name='attendance_details'),
    path('api/logs/', views.AttendanceLogListViewSet.as_view({'get': 'list'}), name='attendance-logs-api'),
    
    # Ramadan Period URLs
    path('ramadan_periods/', views.ramadan_periods, name='ramadan_periods'),
    path('ramadan_period_add/', views.ramadan_period_add, name='ramadan_period_add'),
    path('ramadan_period_detail/<int:pk>/', views.ramadan_period_detail, name='ramadan_period_detail'),
]

# Add the router URLs to the urlpatterns
urlpatterns += router.urls
