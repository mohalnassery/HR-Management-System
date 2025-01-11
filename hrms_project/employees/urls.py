from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views

app_name = 'employees'

# Create a router for API views
router = DefaultRouter()
router.register(r'asset-types', api_views.AssetTypeViewSet, basename='asset-type')
router.register(r'employee-assets', api_views.EmployeeAssetViewSet, basename='employee-asset')

urlpatterns = [
    # Include API URLs under /api/ namespace
    path('api/', include(router.urls)),

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

    # Employee Assets
    path('<int:employee_id>/assets/add/', api_views.add_employee_asset, name='add_employee_asset'),
    path('<int:employee_id>/assets/<int:asset_id>/', api_views.get_employee_asset, name='get_employee_asset'),
    path('<int:employee_id>/assets/<int:asset_id>/edit/', api_views.edit_employee_asset, name='edit_employee_asset'),
    path('<int:employee_id>/assets/<int:asset_id>/return/', api_views.return_employee_asset, name='return_employee_asset'),
    path('<int:employee_id>/assets/<int:asset_id>/delete/', api_views.delete_employee_asset, name='delete_employee_asset'),

    # Document Management
    path('<int:employee_id>/documents/', views.employee_documents, name='employee_documents'),
    path('<int:employee_id>/documents/add/', views.add_document, name='add_document'),
    path('<int:employee_id>/documents/<int:document_id>/edit/', views.edit_document, name='edit_document'),
    path('<int:employee_id>/documents/<int:document_id>/delete/', views.delete_document, name='delete_document'),
    path('<int:employee_id>/documents/<int:document_id>/view/', views.view_document, name='view_document'),

    # Scanner functionality
    path('scan-document/', views.scan_document, name='scan_document_universal'),  # Universal scanner endpoint
    path('<int:employee_id>/scan-document/', views.scan_document, name='scan_document'),  # For backward compatibility
    path('<int:employee_id>/dependents/<int:dependent_id>/scan-document/', views.scan_document, name='scan_dependent_document'),  # For dependent documents

    # Dependent Management
    path('<int:employee_id>/dependents/add/', views.add_dependent, name='add_dependent'),
    path('<int:employee_id>/dependents/<int:dependent_id>/edit/', views.edit_dependent, name='edit_dependent'),
    path('<int:employee_id>/dependents/<int:dependent_id>/delete/', views.delete_dependent, name='delete_dependent'),
    path('<int:employee_id>/dependents/<int:dependent_id>/documents/', views.dependent_documents, name='dependent_documents'),
    path('<int:employee_id>/dependents/<int:dependent_id>/documents/list/', views.get_dependent_documents, name='get_dependent_documents'),
    path('<int:employee_id>/dependents/<int:dependent_id>/documents/add/', views.add_dependent_document, name='add_dependent_document'),
    path('<int:employee_id>/dependents/<int:dependent_id>/documents/<int:document_id>/edit/', views.edit_dependent_document, name='edit_dependent_document'),
    path('<int:employee_id>/dependents/<int:dependent_id>/documents/<int:document_id>/delete/', views.delete_dependent_document, name='delete_dependent_document'),
    path('<int:employee_id>/dependents/<int:dependent_id>/documents/<int:document_id>/view/', views.view_dependent_document, name='view_dependent_document'),

    # Offence URLs
    path('employees/<int:employee_id>/offences/', api_views.employee_offences, name='employee_offences'),
    path('employees/<int:employee_id>/offences/<int:offence_id>/', api_views.employee_offence_detail, name='employee_offence_detail'),
    path('employees/<int:employee_id>/offences/<int:offence_id>/cancel/', api_views.cancel_offence, name='cancel_offence'),
    path('employees/<int:employee_id>/offences/<int:offence_id>/documents/', api_views.add_offence_document, name='add_offence_document'),

    # Bulk Status Change
    path('bulk-status-change/', views.bulk_status_change, name='bulk_status_change'),
    path('bulk-status-change/<str:status>/', views.bulk_status_change, name='bulk_status_change_with_status'),

    # System Info
    path('system-info/', views.system_info, name='system_info'),

    # Function-based views (alternative)
    # path('', views.employee_list, name='employee_list'),
    # path('<int:pk>/', views.employee_detail, name='employee_detail'),
    # path('create/', views.employee_create, name='employee_create'),
    # path('<int:pk>/update/', views.employee_update, name='employee_update'),
    # path('<int:pk>/delete/', views.employee_delete, name='employee_delete'),
]
