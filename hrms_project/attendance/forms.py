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
    leave_sub_type = forms.ChoiceField(
        choices=[],  # Will be populated dynamically
        required=False,
        label='Leave Sub Type',  # Give it a default label
        widget=forms.Select()
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
            'leave_sub_type',
            'start_date',
            'end_date',
            'reason'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        leave_type = self.data.get('leave_type') if self.data else None
        
        # Initialize with empty choices
        self.fields['leave_sub_type'].choices = [('', 'Select type')]
        
        # Set initial choices based on leave type
        if leave_type:
            self.set_sub_type_choices(leave_type)

    def set_sub_type_choices(self, leave_type_id):
        """Set sub-type choices based on leave type"""
        try:
            leave_type = LeaveType.objects.get(id=leave_type_id)
            choices = [('', 'Select type')]  # Always include the empty choice
            
            if leave_type.code == 'ANNUAL':
                choices.extend([
                    ('full_day', 'Full Day'),
                    ('half_day', 'Half Day'),
                ])
            elif leave_type.code == 'HALF':
                choices.extend([
                    ('morning', 'Morning'),
                    ('afternoon', 'Afternoon'),
                ])
            elif leave_type.code == 'MATERNITY':
                choices.extend([
                    ('paid_60', '60 days (Full Pay)'),
                    ('unpaid_15', 'Additional 15 days (Unpaid)'),
                ])
            elif leave_type.code == 'DEATH':
                choices.extend([
                    ('spouse_30', 'Woman\'s Husband (30 days)'),
                    ('spouse_3', 'Man\'s Wife (3 days)'),
                    ('first_degree', 'First Degree Relative (3 days)'),
                    ('second_degree', 'Second Degree Spouse Relative (3 days)'),
                ])
            elif leave_type.code == 'SICK':
                choices.extend([
                    ('tier1', 'First 15 days - Full Pay'),
                    ('tier2', 'Next 20 days - Half Pay'),
                    ('tier3', 'Next 20 days - Unpaid'),
                ])
            elif leave_type.code == 'MARRIAGE':
                choices.extend([('3_days', '3 days')])
            elif leave_type.code == 'PATERNITY':
                choices.extend([('1_day', '1 day')])
            elif leave_type.code == 'HAJJ':
                choices.extend([('14_days', '14 days (Full Pay)')])
            elif leave_type.code == 'IDDAH':
                choices.extend([
                    ('paid_30', '1 month (Full Pay)'),
                    ('unpaid_100', '3 months and 10 Days (Unpaid)'),
                ])
                
            self.fields['leave_sub_type'].choices = choices
            self.fields['leave_sub_type'].required = len(choices) > 1  # Required if there are choices other than the empty option
            self.fields['leave_sub_type'].label = f'{leave_type.name} Type' if len(choices) > 1 else ''
                
        except LeaveType.DoesNotExist:
            self.fields['leave_sub_type'].choices = [('', 'Select type')]
            self.fields['leave_sub_type'].required = False
            self.fields['leave_sub_type'].label = ''

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        leave_type = cleaned_data.get('leave_type')
        leave_sub_type = cleaned_data.get('leave_sub_type')

        if start_date and end_date:
            # Ensure end date is never less than start date
            if end_date < start_date:
                # Automatically adjust end date to match start date
                cleaned_data['end_date'] = start_date
                end_date = start_date
                # Add a message to the form to inform the user
                self.add_error('end_date', 'End date cannot be earlier than start date. It has been adjusted automatically.')
            
            # Validate date range
            self.validate_date_range(
                start_date,
                end_date,
                allow_single_day=True,
                allow_past_dates=True
            )

            # Additional validation for half-day leave
            if leave_sub_type in ['half_day', 'morning', 'afternoon'] and start_date != end_date:
                raise forms.ValidationError('Half day leave must be for a single day')

            # Validate leave sub-type is provided when required
            if leave_type and leave_type.code in ['ANNUAL', 'HALF', 'MATERNITY', 'DEATH', 'SICK', 'MARRIAGE', 'PATERNITY', 'HAJJ', 'IDDAH'] and not leave_sub_type:
                raise forms.ValidationError('Please select the leave sub-type')

        return cleaned_data