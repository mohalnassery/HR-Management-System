from django import forms
from .models import Holiday

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