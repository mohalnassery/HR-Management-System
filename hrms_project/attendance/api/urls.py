from django.urls import path
from . import views
from .leave_api_views import validate_leave_request

app_name = 'attendance_api'

urlpatterns = [
    path('shift-assignments/', views.shift_assignments, name='shift_assignments'),
    path('validate-leave-request/', validate_leave_request, name='validate_leave_request'),
]
