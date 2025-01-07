from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    # Class-based views
    path('', views.EmployeeListView.as_view(), name='employee_list'),
    path('<int:pk>/', views.EmployeeDetailView.as_view(), name='employee_detail'),
    path('create/', views.EmployeeCreateView.as_view(), name='employee_create'),
    path('<int:pk>/update/', views.EmployeeUpdateView.as_view(), name='employee_update'),
    path('<int:pk>/delete/', views.EmployeeDeleteView.as_view(), name='employee_delete'),

    # Bank Account Management
    path('<int:employee_id>/bank-accounts/add/', views.add_bank_account, name='add_bank_account'),
    path('<int:employee_id>/bank-accounts/<int:account_id>/edit/', views.edit_bank_account, name='edit_bank_account'),
    path('<int:employee_id>/bank-accounts/<int:account_id>/delete/', views.delete_bank_account, name='delete_bank_account'),

    # Document Management
    path('<int:employee_id>/documents/add/', views.add_document, name='add_document'),
    path('<int:employee_id>/documents/<int:document_id>/edit/', views.edit_document, name='edit_document'),
    path('<int:employee_id>/documents/<int:document_id>/delete/', views.delete_document, name='delete_document'),
    path('<int:employee_id>/documents/<int:document_id>/view/', views.view_document, name='view_document'),
    path('employee/<int:employee_id>/scan-document/', views.scan_document, name='scan_document'),

    # Bulk Status Change
    path('bulk-status-change/', views.bulk_status_change, name='bulk_status_change'),
    path('bulk-status-change/<str:status>/', views.bulk_status_change, name='bulk_status_change_with_status'),

    # System Info
    path('system-info/', views.get_system_info, name='system_info'),

    # Function-based views (alternative)
    # path('', views.employee_list, name='employee_list'),
    # path('<int:pk>/', views.employee_detail, name='employee_detail'),
    # path('create/', views.employee_create, name='employee_create'),
    # path('<int:pk>/update/', views.employee_update, name='employee_update'),
    # path('<int:pk>/delete/', views.employee_delete, name='employee_delete'),
]
