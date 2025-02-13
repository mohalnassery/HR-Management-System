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