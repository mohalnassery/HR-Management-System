from django.urls import path
from . import views

app_name = 'attendance_api'

urlpatterns = [
    path('shift-assignments/', views.shift_assignments, name='shift_assignments'),
]
