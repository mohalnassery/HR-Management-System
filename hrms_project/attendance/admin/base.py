from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from typing import Optional, Tuple, List

from ..utils.display import DisplayFormatter

class BaseModelAdmin(admin.ModelAdmin):
    """
    Base admin class with common functionality for all admin views.
    """
    list_per_page = 25
    
    def get_ordering(self, request) -> Tuple:
        """Default to created_at descending if model has this field"""
        if hasattr(self.model, 'created_at'):
            return ('-created_at',)
        return super().get_ordering(request)

class EmployeeLinkedModelAdmin(BaseModelAdmin):
    """
    Admin class for models that have an employee relationship.
    Provides employee link functionality.
    """
    def get_search_fields(self, request) -> List[str]:
        """Add employee-related search fields"""
        fields = super().get_search_fields(request) or []
        fields.extend([
            'employee__first_name',
            'employee__last_name',
            'employee__employee_number'
        ])
        return fields

    def get_list_filter(self, request) -> List[str]:
        """Add created_at to list filters if available"""
        filters = super().get_list_filter(request) or []
        if hasattr(self.model, 'created_at'):
            filters = list(filters)
            filters.append('created_at')
        return filters

    def employee_link(self, obj) -> str:
        """Generate a link to the employee admin page"""
        if obj.employee:
            url = reverse('admin:employees_employee_change', args=[obj.employee.id])
            return format_html('<a href="{}">{}</a>', url, obj.employee)
        return '-'
    employee_link.short_description = 'Employee'

class PeriodModelAdmin(BaseModelAdmin):
    """
    Admin class for models with start/end date periods.
    Provides period display and filtering functionality.
    """
    date_hierarchy = 'start_date'

    def get_list_filter(self, request) -> List[str]:
        """Add period-related filters"""
        filters = super().get_list_filter(request) or []
        filters = list(filters)
        if hasattr(self.model, 'is_active'):
            filters.append('is_active')
        return filters

    def period_display(self, obj) -> str:
        """Display the period using the centralized formatter"""
        return DisplayFormatter.period_display(
            obj.start_date,
            getattr(obj, 'end_date', None),
            getattr(obj, 'is_permanent', False)
        )
    period_display.short_description = 'Period'

class ColorCodedStatusMixin:
    """
    Mixin that provides color-coded status display functionality.
    """
    def status_display(self, obj) -> str:
        """
        Display the status with color coding.
        Requires STATUS_CHOICES on the model and status_colors in the admin class.
        """
        if not hasattr(self, 'status_colors'):
            raise AttributeError(
                f"{self.__class__.__name__} must define status_colors dictionary mapping "
                "status values to colors"
            )
            
        status_dict = dict(getattr(obj, 'STATUS_CHOICES', ()))
        if not status_dict:
            raise AttributeError(
                f"{obj.__class__.__name__} must define STATUS_CHOICES"
            )
            
        return DisplayFormatter.color_coded_display(
            obj.status,
            status_dict.get(obj.status, obj.status),
            self.status_colors
        )
    status_display.short_description = 'Status'
