from django import forms
from django.core.validators import FileExtensionValidator
from typing import Dict, Any, Optional
from datetime import date
from .models import Holiday, Leave, LeaveType, LeaveDocument

class BaseForm(forms.Form):
    """
    Base form class that provides common functionality for all forms.
    Automatically adds Bootstrap classes to form widgets.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_bootstrap_classes()
    
    def _add_bootstrap_classes(self):
        """Add Bootstrap classes to form widgets based on their type"""
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                self._add_widget_class(widget, 'form-select')
            elif isinstance(widget, forms.CheckboxInput):
                self._add_widget_class(widget, 'form-check-input')
            elif isinstance(widget, forms.FileInput):
                self._add_widget_class(widget, 'form-control')
            else:
                self._add_widget_class(widget, 'form-control')
    
    @staticmethod
    def _add_widget_class(widget: forms.Widget, class_name: str):
        """Add a CSS class to a widget if it doesn't already have it"""
        if 'class' in widget.attrs:
            if class_name not in widget.attrs['class']:
                widget.attrs['class'] += f' {class_name}'
        else:
            widget.attrs['class'] = class_name

class BaseModelForm(forms.ModelForm, BaseForm):
    """
    Base model form class that combines ModelForm functionality with BaseForm.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_bootstrap_classes()

class DateRangeValidationMixin:
    """
    Mixin to provide date range validation functionality.
    Can be used with both forms and serializers.
    """
    
    def validate_date_range(
        self,
        start_date: date,
        end_date: date,
        allow_single_day: bool = True,
        allow_past_dates: bool = True,
        max_days: Optional[int] = None
    ) -> None:
        """
        Validate a date range according to specified constraints.
        
        Args:
            start_date: The start date of the range
            end_date: The end date of the range
            allow_single_day: Whether the start and end date can be the same
            allow_past_dates: Whether dates in the past are allowed
            max_days: Maximum number of days allowed between start and end date
            
        Raises:
            ValidationError: If the date range is invalid
        """
        if not start_date or not end_date:
            return
            
        if start_date > end_date:
            raise forms.ValidationError('End date must be after start date')
            
        if not allow_single_day and start_date == end_date:
            raise forms.ValidationError('Start and end date cannot be the same')
            
        if not allow_past_dates and start_date < date.today():
            raise forms.ValidationError('Past dates are not allowed')
            
        if max_days:
            days_difference = (end_date - start_date).days + 1
            if days_difference > max_days:
                raise forms.ValidationError(
                    f'Date range cannot exceed {max_days} days'
                )

class HolidayForm(BaseModelForm):
    class Meta:
        model = Holiday
        fields = [
            'name',
            'date',
            'holiday_type',
            'description',
            'is_recurring',
            'is_paid',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class LeaveBalanceUploadForm(BaseForm):
    csv_file = forms.FileField(
        label="CSV File",
        help_text="Upload a CSV file with employee_number and leave_balance columns."
    )
    as_of_date = forms.DateField(
        label="Balance as of Date",
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Date to associate with these beginning balances."
    )
    leave_type_code = forms.CharField(
        label="Leave Type Code",
        initial='ANNUAL',
        widget=forms.HiddenInput(),
    )

class LeaveRequestForm(BaseModelForm, DateRangeValidationMixin):
    duration_type = forms.ChoiceField(
        choices=[
            ('full_day', 'Full Day'),
            ('half_day', 'Half Day'),
        ],
        initial='full_day',
        widget=forms.Select()  # Bootstrap class will be added automatically
    )
    
    document = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        help_text='Supported formats: PDF, JPG, JPEG, PNG'
    )

    class Meta:
        model = Leave
        fields = [
            'leave_type',
            'duration_type',
            'start_date',
            'end_date',
            'reason'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3})
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        duration_type = cleaned_data.get('duration_type')

        if start_date and end_date:
            # Validate date range
            self.validate_date_range(
                start_date,
                end_date,
                allow_single_day=True,
                allow_past_dates=True
            )

            # Additional validation for half-day leave
            if duration_type == 'half_day' and start_date != end_date:
                raise forms.ValidationError('Half day leave must be for a single day')

        return cleaned_data