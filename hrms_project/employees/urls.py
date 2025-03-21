from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views

app_name = 'employees'

# Create a router for API views
router = DefaultRouter()
router.register(r'asset-types', api_views.AssetTypeViewSet, basename='asset-type')
router.register(r'employee-assets', api_views.EmployeeAssetViewSet, basename='employee-asset')
router.register(r'offense-rules', api_views.OffenseRuleViewSet, basename='offense-rule')
router.register(r'employee-offenses', api_views.EmployeeOffenseViewSet, basename='employee-offense')

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

    # Salary Management
    path('<int:employee_id>/salary/add/', views.add_salary, name='add_salary'),
    path('salary/<int:salary_id>/edit/', views.edit_salary, name='edit_salary'),
    path('<int:employee_id>/salary/revision/add/', views.add_salary_revision, name='add_salary_revision'),
    path('<int:employee_id>/salary/certificate/request/', views.request_certificate, name='request_certificate'),

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

    # Offence Management URLs
    path('api/offenses/', api_views.EmployeeOffenseViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='offense_list_create'),
    
    path('api/offenses/<int:pk>/', api_views.EmployeeOffenseViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='offense_detail'),

    # employee-specific offense URLs
    path('api/employees/<int:employee_id>/offenses/', api_views.employee_offenses, name='employee_offenses'),
    path('api/employees/<int:employee_id>/offenses/<int:offense_id>/', api_views.employee_offense_detail, name='employee_offense_detail'),
    # count offenses
    path('api/employee-offenses/<int:employee_id>/count/', api_views.get_employee_offense_count, name='get_employee_offense_count'),
    
    # Offense Actions
    path('api/offenses/<int:pk>/status/', api_views.update_offense_status, name='offense_status_update'),
    path('api/offenses/<int:pk>/payment/', api_views.record_offense_payment, name='offense_payment'),
    path('api/offenses/<int:pk>/print/', api_views.print_offense, name='offense_print'),
    
    # Employee-specific Offense URLs
    path('api/employees/<int:employee_id>/offenses/', api_views.employee_offenses, name='employee_offenses'),
    path('api/employees/<int:employee_id>/offenses/count/', api_views.get_employee_offense_count, name='employee_offense_count'),
    
    # Offense Rules
    path('api/offense-rules/', api_views.OffenseRuleViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='offense_rule_list'),
    
    path('api/offense-rules/<int:pk>/', api_views.OffenseRuleViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='offense_rule_detail'),

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
