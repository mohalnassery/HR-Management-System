from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('', views.payroll_list, name='payroll_list'),
    path('generate/', views.generate_payroll, name='generate_payroll'),
    path('payslip/<int:pk>/', views.payslip_detail, name='payslip_detail'),
    path('settings/', views.payroll_settings, name='payroll_settings'),
]
