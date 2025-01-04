from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Department, Division, Location, Bank, Employee,
    EmployeeDependent, EmergencyContact, EmployeeDocument,
    EmployeeAsset, EmployeeEducation, EmployeeOffence, LifeEvent
)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ar', 'code', 'parent', 'manager')
    search_fields = ('name', 'name_ar', 'code')
    list_filter = ('parent',)

@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ar', 'code', 'department')
    search_fields = ('name', 'name_ar', 'code')
    list_filter = ('department',)

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code', 'address')

@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'swift_code')
    search_fields = ('name', 'swift_code')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_number', 'get_full_name', 'department', 'division', 'email', 'is_active')
    list_filter = ('is_active', 'department', 'contract_type', 'employee_category', 'in_probation')
    search_fields = ('employee_number', 'first_name', 'last_name', 'email', 'cpr_number')
    fieldsets = (
        ('Personal Information', {
            'fields': (
                ('first_name', 'middle_name', 'last_name'),
                ('first_name_ar', 'middle_name_ar', 'last_name_ar'),
                ('date_of_birth', 'gender', 'marital_status'),
                ('nationality', 'religion'),
                'email',
            )
        }),
        ('Employment Information', {
            'fields': (
                'employee_number',
                ('department', 'division'),
                ('location', 'manager'),
                'is_manager',
                ('contract_type', 'employee_category'),
                ('joined_date', 'rejoined_date'),
                ('in_probation', 'probation_period'),
                ('cost_center', 'profit_center'),
                'payroll_group',
            )
        }),
        ('Identification', {
            'fields': (
                'cpr_number',
                'profession_cpr',
                'education_category',
            )
        }),
        ('Visa & Accommodation', {
            'fields': (
                'company_accommodation',
                'visa_cr_number',
                'sponsor_name',
                'accom_occu_date',
            )
        }),
        ('Bank Details', {
            'fields': (
                'bank',
                'account_number',
                'iban',
            )
        }),
        ('Contract Details', {
            'fields': (
                ('contract_start_date', 'contract_end_date'),
                'notice_period',
                'leave_accrual_rate',
            )
        }),
        ('Salary Information', {
            'fields': (
                'basic_salary',
                'total_allowances',
                'total_deductions',
            ),
            'classes': ('collapse',),
        }),
        ('Bond Details', {
            'fields': (
                'bond_amount',
                'guarantee_details',
            ),
            'classes': ('collapse',),
        }),
    )

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Full Name'

@admin.register(EmployeeDependent)
class EmployeeDependentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'name', 'relationship', 'date_of_birth', 'is_sponsored')
    list_filter = ('relationship', 'is_sponsored')
    search_fields = ('name', 'employee__first_name', 'employee__last_name')

@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ('employee', 'name', 'relationship', 'phone_number')
    search_fields = ('name', 'phone_number', 'employee__first_name', 'employee__last_name')

@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'document_type', 'document_number', 'issue_date', 'expiry_date')
    list_filter = ('document_type',)
    search_fields = ('document_number', 'employee__first_name', 'employee__last_name')

@admin.register(EmployeeAsset)
class EmployeeAssetAdmin(admin.ModelAdmin):
    list_display = ('employee', 'asset_name', 'asset_number', 'issue_date', 'return_date')
    search_fields = ('asset_name', 'asset_number', 'employee__first_name', 'employee__last_name')

@admin.register(EmployeeEducation)
class EmployeeEducationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'degree', 'institution', 'graduation_year', 'gpa', 'major')
    search_fields = ('employee__first_name', 'employee__last_name', 'institution', 'degree', 'major')
    list_filter = ('degree', 'graduation_year')

@admin.register(EmployeeOffence)
class EmployeeOffenceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'severity', 'action_taken')
    list_filter = ('severity',)
    search_fields = ('employee__first_name', 'employee__last_name')

@admin.register(LifeEvent)
class LifeEventAdmin(admin.ModelAdmin):
    list_display = ('employee', 'event_type', 'date')
    list_filter = ('event_type',)
    search_fields = ('employee__first_name', 'employee__last_name')
