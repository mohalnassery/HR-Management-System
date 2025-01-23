from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'attendance'

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'shifts', views.ShiftViewSet, basename='shift')
router.register(r'attendance', views.AttendanceViewSet, basename='attendance')
router.register(r'leaves', views.LeaveViewSet, basename='leave')
router.register(r'holidays', views.HolidayViewSet, basename='holiday')
router.register(r'attendance-list', views.AttendanceListViewSet, basename='attendance-list')

urlpatterns = [
    # Template views
    path('', views.attendance_list, name='attendance_list'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('mark/', views.mark_attendance, name='mark_attendance'),
    path('upload/', views.upload_attendance, name='upload_attendance'),
    path('detail/<int:attendance_id>/', views.attendance_detail_view, name='attendance_detail'),
    path('leaves/', views.leave_request_list, name='leave_request_list'),
    path('leaves/create/', views.leave_request_create, name='leave_request_create'),
    path('leaves/<int:pk>/', views.leave_request_detail, name='leave_request_detail'),

    # API endpoints
    path('api/', include(router.urls)),
    path('api/attendance/<int:attendance_id>/details/', views.attendance_detail_api, name='attendance-detail-api'),
    path('api/search-employees/', views.search_employees, name='search_employees'),
    path('api/calendar-events/', views.calendar_events, name='calendar_events'),
    path('api/employee/<int:employee_id>/attendance/', views.get_employee_attendance, name='employee-attendance'),
    path('api/attendance/<int:record_id>/', views.attendance_record_api, name='attendance-record-api'),
    path('api/attendance/', views.add_attendance_record, name='add-attendance-record'),
]
