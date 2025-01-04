from django.contrib import admin
from .models import (
    Department, Division, Location, Employee, EmployeeDependent,
    EmergencyContact, EmployeeDocument, EmployeeAsset, EmployeeEducation,
    EmployeeOffence, LifeEvent, EmployeeBankAccount, CostProfitCenter
)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ar', 'code', 'parent')
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

@admin.register(CostProfitCenter)
class CostProfitCenterAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('is_active',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_number', 'get_full_name', 'designation', 'department', 'is_active')
    search_fields = ('employee_number', 'first_name', 'last_name', 'email')
    list_filter = ('is_active', 'department', 'division', 'employee_category', 'in_probation')
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                ('employee_number', 'profile_picture'),
                ('first_name', 'middle_name', 'last_name'),
                ('first_name_ar', 'middle_name_ar', 'last_name_ar'),
                ('date_of_birth', 'gender'),
                ('nationality', 'religion'),
                ('marital_status', 'education_category'),
                ('cpr_number', 'email'),
                'in_probation'
            )
        }),
        ('Employment Information', {
            'fields': (
                ('designation', 'department'),
                ('division', 'location'),
                ('contract_type', 'joined_date'),
                ('cost_center', 'profit_center'),
                'employee_category',
                'is_active'
            )
        })
    )

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'

@admin.register(EmployeeBankAccount)
class EmployeeBankAccountAdmin(admin.ModelAdmin):
    list_display = ('employee', 'bank', 'account_number', 'iban')
    search_fields = ('employee__employee_number', 'bank', 'account_number', 'iban')
    list_filter = ('bank',)

@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'document_type', 'document_number', 'issue_date', 'expiry_date')
    search_fields = ('employee__employee_number', 'document_type', 'document_number')
    list_filter = ('document_type', 'issue_date', 'expiry_date')

@admin.register(EmployeeDependent)
class EmployeeDependentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'name', 'relationship', 'is_sponsored')
    search_fields = ('employee__employee_number', 'name')
    list_filter = ('relationship', 'is_sponsored')

@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ('employee', 'name', 'relationship', 'phone_number')
    search_fields = ('employee__employee_number', 'name', 'phone_number')

@admin.register(EmployeeAsset)
class EmployeeAssetAdmin(admin.ModelAdmin):
    list_display = ('employee', 'asset_name', 'asset_number', 'issue_date', 'return_date')
    search_fields = ('employee__employee_number', 'asset_name', 'asset_number')
    list_filter = ('issue_date', 'return_date')

@admin.register(EmployeeEducation)
class EmployeeEducationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'institution', 'degree', 'graduation_year')
    search_fields = ('employee__employee_number', 'institution', 'degree')
    list_filter = ('graduation_year',)

@admin.register(EmployeeOffence)
class EmployeeOffenceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'severity')
    search_fields = ('employee__employee_number',)
    list_filter = ('date', 'severity')

@admin.register(LifeEvent)
class LifeEventAdmin(admin.ModelAdmin):
    list_display = ('employee', 'event_type', 'date')
    search_fields = ('employee__employee_number',)
    list_filter = ('event_type', 'date')
