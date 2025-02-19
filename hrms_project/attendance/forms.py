from django import forms
from django.core.validators import FileExtensionValidator
from .models import Holiday, Leave, LeaveType, LeaveDocument

class HolidayForm(forms.ModelForm):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'form-control'})
        self.fields['date'].widget.attrs.update({'class': 'form-control'})
        self.fields['holiday_type'].widget.attrs.update({'class': 'form-select'})
        self.fields['description'].widget.attrs.update({'class': 'form-control'}) 

class LeaveBalanceUploadForm(forms.Form):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['csv_file'].widget.attrs.update({'class': 'form-control'})
        self.fields['as_of_date'].widget.attrs.update({'class': 'form-control'})

class LeaveRequestForm(forms.ModelForm):
    duration_type = forms.ChoiceField(
        choices=[
            ('full_day', 'Full Day'),
            ('half_day', 'Half Day'),
        ],
        initial='full_day',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    document = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
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
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        duration_type = cleaned_data.get('duration_type')

        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError('End date must be after start date')

            if duration_type == 'half_day' and start_date != end_date:
                raise forms.ValidationError('Half day leave must be for a single day')

        return cleaned_data