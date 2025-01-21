from django.contrib import admin
from .models import (
    Department, Division, Location, Employee, EmployeeDependent,
    EmergencyContact, EmployeeDocument, EmployeeAsset, EmployeeEducation,
    EmployeeOffence, LifeEvent, EmployeeBankAccount, CostProfitCenter,
    DependentDocument, OffenseRule
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
    list_display = ('employee', 'name', 'relation', 'date_of_birth', 'valid_passage')
    search_fields = ('employee__employee_number', 'name', 'passport_number', 'cpr_number')
    list_filter = ('relation', 'valid_passage')

@admin.register(DependentDocument)
class DependentDocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'document_type', 'document_number', 'issue_date', 'expiry_date', 'status']
    list_filter = ['document_type', 'status', 'nationality']
    search_fields = ['name', 'document_number']
    date_hierarchy = 'created_at'

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

@admin.register(OffenseRule)
class OffenseRuleAdmin(admin.ModelAdmin):
    list_display = ('rule_id', 'group', 'name', 'first_penalty', 'second_penalty', 'third_penalty', 'fourth_penalty', 'is_active')
    list_filter = ('group', 'is_active')
    search_fields = ('rule_id', 'name', 'description')
    ordering = ('group', 'rule_id')
    fieldsets = (
        (None, {
            'fields': ('rule_id', 'group', 'name', 'description')
        }),
        ('Penalties', {
            'fields': ('first_penalty', 'second_penalty', 'third_penalty', 'fourth_penalty')
        }),
        ('Additional Information', {
            'fields': ('remarks', 'is_active')
        })
    )

@admin.register(EmployeeOffence)
class EmployeeOffenceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'rule', 'offense_date', 'offense_count', 'applied_penalty', 'is_acknowledged')
    list_filter = ('offense_date', 'rule__group', 'is_acknowledged')
    search_fields = ('employee__first_name', 'employee__last_name', 'rule__name', 'details')
    raw_id_fields = ('employee', 'rule')
    readonly_fields = ('offense_count', 'original_penalty', 'created_by', 'modified_by', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('employee', 'rule', 'offense_date', 'offense_count')
        }),
        ('Penalty Information', {
            'fields': ('original_penalty', 'applied_penalty', 'details')
        }),
        ('Documents', {
            'fields': ('warning_letter', 'acknowledgment', 'is_acknowledged', 'acknowledged_at')
        }),
        ('Audit Trail', {
            'fields': ('created_by', 'modified_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(LifeEvent)
class LifeEventAdmin(admin.ModelAdmin):
    list_display = ('employee', 'event_type', 'date')
    search_fields = ('employee__employee_number',)
    list_filter = ('event_type', 'date')
