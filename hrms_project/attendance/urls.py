from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views  

from .views import shifts_views
from .views import attendance_views
from .views import calendar_views
from .views import leave_views
from .views import holiday_views
from .views import ramadan_views
from .api import report_views

app_name = 'attendance'

# Create a router and register the ViewSets
router = DefaultRouter()
router.register(r'api/shifts', shifts_views.ShiftViewSet, basename='shift')
router.register(r'api/attendance_records', attendance_views.AttendanceRecordViewSet, basename='attendancerecord')
router.register(r'api/attendance_logs', attendance_views.AttendanceLogListViewSet, basename='attendancelog')
router.register(r'api/leaves', leave_views.LeaveViewSet, basename='leave')
router.register(r'api/holidays', holiday_views.HolidayViewSet, basename='holiday')
router.register(r'api/reports', report_views.ReportViewSet, basename='report')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Report URLs
    path('attendance_report/', attendance_views.attendance_report, name='attendance_report'),
    path('attendance_detail/', attendance_views.attendance_detail_view, name='attendance_detail'),
    path('api/details/', attendance_views.attendance_detail_api, name='attendance_detail_api'),
    path('api/reports/export/', report_views.ReportViewSet.as_view({'get': 'export'}), name='report-export'),
    
    # Attendance URLs
    path('attendance_list/', attendance_views.attendance_list, name='attendance_list'),
    path('mark_attendance/', attendance_views.mark_attendance, name='mark_attendance'),
    path('upload_attendance/', attendance_views.upload_attendance, name='upload_attendance'),
    path('reprocess_attendance/', attendance_views.reprocess_attendance_view, name='reprocess_attendance'),
    
    # Calendar URLs
    path('calendar/', calendar_views.calendar_view, name='calendar'),
    path('calendar/month/', calendar_views.calendar_month, name='calendar_month'),
    path('calendar/week/', calendar_views.calendar_week, name='calendar_week'),
    path('calendar/department/', calendar_views.calendar_department, name='calendar_department'),
    path('api/calendar_events/', calendar_views.calendar_events, name='calendar_events'),
    
    # Leave Management URLs
    path('leave_request_list/', leave_views.leave_request_list, name='leave_request_list'),
    path('leave_request_create/', leave_views.leave_request_create, name='leave_request_create'),
    path('leave_request_detail/<int:pk>/', leave_views.leave_request_detail, name='leave_request_detail'),
    path('leave_balance/', leave_views.leave_balance, name='leave_balance'),
    path('leave_types/', leave_views.leave_types, name='leave_types'),
    path('api/leaves/<int:pk>/approve/', leave_views.leave_request_action, {'action': 'approve'}, name='leave_request_approve'),
    path('api/leaves/<int:pk>/reject/', leave_views.leave_request_action, {'action': 'reject'}, name='leave_request_reject'),
    path('api/leaves/<int:pk>/cancel/', leave_views.leave_request_action, {'action': 'cancel'}, name='leave_request_cancel'),
    path('api/leaves/<int:pk>/delete/', leave_views.leave_request_action, {'action': 'delete'}, name='leave_request_delete'),
    
    # Holiday Management URLs
    path('holiday_list/', holiday_views.holiday_list, name='holiday_list'),
    path('holiday_create/', holiday_views.holiday_create, name='holiday_create'),
    path('holiday_edit/<int:pk>/', holiday_views.holiday_edit, name='holiday_edit'),
    path('holiday_delete/<int:pk>/', holiday_views.holiday_delete, name='holiday_delete'),
    path('preview_next_year_holidays/', holiday_views.preview_next_year_holidays, name='preview_next_year_holidays'),
    path('generate_next_year_holidays/', holiday_views.generate_next_year_holidays, name='generate_next_year_holidays'),
    path('recurring_holidays/', holiday_views.recurring_holidays, name='recurring_holidays'),
    
    # Shift Management URLs
    path('shifts/', shifts_views.shift_list, name='shift_list'),
    path('shifts/create/', shifts_views.shift_create, name='shift_create'),
    path('shifts/<int:pk>/edit/', shifts_views.shift_edit, name='shift_edit'),
    path('shifts/day/<str:date>/', shifts_views.shift_day_detail, name='shift_day_detail'),
    path('shift-assignments/', shifts_views.shift_assignment_list, name='shift_assignment_list'),
    path('shift-assignments/create/', shifts_views.shift_assignment_create, name='shift_assignment_create'),
    path('shift-assignments/<int:pk>/edit/', shifts_views.shift_assignment_edit, name='shift_assignment_edit'),
    path('shift-assignments/<int:pk>/delete/', shifts_views.shift_assignment_delete, name='shift_assignment_delete'),
    
    # API Endpoints
    path('api/get_calendar_events/', views.get_calendar_events, name='get_calendar_events'),
    path('api/get_employee_attendance/<int:employee_id>/', views.get_employee_attendance, name='get_employee_attendance'),
    path('api/attendance_record/<int:record_id>/', views.attendance_record_api, name='attendance_record_api'),
    path('api/add_attendance_record/', views.add_attendance_record, name='add_attendance_record'),
    path('api/search_employees/', views.search_employees, name='search_employees'),
    path('api/attendance_details/', views.attendance_details, name='attendance_details'),
    path('api/employee/<int:employee_id>/shifts/', shifts_views.get_employee_shifts, name='get_employee_shifts'),
    path('api/logs/', attendance_views.AttendanceLogListViewSet.as_view({'get': 'list'}), name='attendance_log_list'),
    path('api/shift_assignment_calendar_events/', shifts_views.shift_assignment_calendar_events, name='shift_assignment_calendar_events'),
    path('api/shift-assignments/quick/', views.quick_shift_assignment, name='quick_shift_assignment'),
    path('api/shift-assignments/<int:pk>/', views.shift_assignment_detail, name='shift_assignment_detail'),
    path('get_department_employees/', views.get_department_employees, name='get_department_employees'),
    path('api/records/upload_excel/', attendance_views.AttendanceRecordViewSet.as_view({'post': 'upload_excel'}), name='upload_excel'),
    
    # Ramadan Period URLs
    path('ramadan_periods/', ramadan_views.RamadanPeriodListView.as_view(), name='ramadan_periods'),
    path('ramadan_period/add/', ramadan_views.RamadanPeriodAddView.as_view(), name='ramadan_period_add'),
    path('ramadan_period/<int:pk>/', ramadan_views.RamadanPeriodDetailView.as_view(), name='ramadan_period_detail'),
    
    # Shift Override URLs
    path('shift_override/', views.create_shift_override, name='shift_override_create'),
    path('shift_override/<str:date>/', views.delete_shift_override, name='shift_override_delete'),
    path('shift_overrides/<int:year>/<int:month>/', views.get_shift_overrides, name='shift_overrides_list'),
]
