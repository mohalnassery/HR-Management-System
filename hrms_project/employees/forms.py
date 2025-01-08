from django import forms
from django.db import transaction
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, HTML, Field, Fieldset
from crispy_forms.bootstrap import Tab, TabHolder
from .models import (
    Employee, Department, Division, EmployeeDependent, 
    EmergencyContact, EmployeeDocument, EmployeeBankAccount,
    CostProfitCenter, DependentDocument
)

class EmployeeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        
        # Make some fields optional
        optional_fields = ['middle_name', 'middle_name_ar', 'religion',
                         'education_category', 'profile_picture']
        
        for field in optional_fields:
            self.fields[field].required = False

        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'form-check-input'
                })
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({
                    'class': 'form-control-file'
                })
            else:
                field.widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': field.label
                })

        # Load related fields efficiently
        self.fields['department'].queryset = Department.objects.all()
        self.fields['division'].queryset = Division.objects.all().select_related('department')
        self.fields['cost_center'].queryset = CostProfitCenter.objects.filter(is_active=True)
        self.fields['profit_center'].queryset = CostProfitCenter.objects.filter(is_active=True)

        # Define form layout
        self.helper.layout = Layout(
            TabHolder(
                Tab('Employee Information',
                    Fieldset('Basic Information',
                        Row(
                            Column('employee_number', css_class='form-group col-md-6'),
                            Column('profile_picture', css_class='form-group col-md-6'),
                            css_class='form-row'
                        ),
                    ),
                    Fieldset('Personal Information (English)',
                        Row(
                            Column('first_name', css_class='form-group col-md-6'),
                            Column('middle_name', css_class='form-group col-md-6'),
                            css_class='form-row'
                        ),
                        Row(
                            Column('last_name', css_class='form-group col-md-6'),
                            css_class='form-row'
                        ),
                    ),
                    Fieldset('Personal Information (Arabic)',
                        Row(
                            Column('first_name_ar', css_class='form-group col-md-6'),
                            Column('middle_name_ar', css_class='form-group col-md-6'),
                            css_class='form-row'
                        ),
                        Row(
                            Column('last_name_ar', css_class='form-group col-md-6'),
                            css_class='form-row'
                        ),
                    ),
                    Fieldset('Demographics',
                        Row(
                            Column('date_of_birth', css_class='form-group col-md-6'),
                            Column('gender', css_class='form-group col-md-6'),
                            css_class='form-row'
                        ),
                        Row(
                            Column('marital_status', css_class='form-group col-md-6'),
                            Column('nationality', css_class='form-group col-md-6'),
                            css_class='form-row'
                        ),
                        Row(
                            Column('religion', css_class='form-group col-md-6'),
                            Column('education_category', css_class='form-group col-md-6'),
                            css_class='form-row'
                        ),
                    ),
                    Fieldset('Contact & Identification',
                        Row(
                            
                            Column('primary_phone', css_class='form-group col-md-6'),
                            Column('secondary_phone', css_class='form-group col-md-6'),

                            css_class='form-row'
                        ),
                        Row(
                            Column('email', css_class='form-group col-md-6'),
                            Column('cpr_number', css_class='form-group col-md-6'),
                            css_class='form-row'
                        ),
                    ),
                ),
                Tab('Employment Information',
                    Fieldset('Position Details',
                        Row(
                            Column('designation', css_class='form-group col-md-6'),
                            Column('employee_category', css_class='form-group col-md-6'),
                            css_class='form-row'
                        ),
                    ),
                    Fieldset('Department & Location',
                        Row(
                            Column('division', css_class='form-group col-md-6'),
                            Column('department', css_class='form-group col-md-6'),
                            css_class='form-row'
                        ),
                        Row(
                            Column('location', css_class='form-group col-md-6'),
                            css_class='form-row'
                        ),
                    ),
                    Fieldset('Contract Information',
                        Row(
                            Column('contract_type', css_class='form-group col-md-6'),
                            Column('joined_date', css_class='form-group col-md-6'),
                            css_class='form-row'
                        ),
                        Row(
                            Column('in_probation', css_class='form-group col-md-6'),
                            css_class='form-row'
                        ),
                    ),
                    Fieldset('Financial Centers',
                        Row(
                            Column('cost_center', css_class='form-group col-md-6'),
                            Column('profit_center', css_class='form-group col-md-6'),
                            css_class='form-row'
                        ),
                    ),
                ),
            ),
            Div(
                Row(
                    Column(Field('is_active'), css_class='form-group col-6'),
                    Column(
                        HTML("""
                            <div class="text-end">
                                <a href="{% url 'employees:employee_list' %}" class="btn btn-secondary">Cancel</a>
                                <button type="submit" class="btn btn-primary">Save</button>
                            </div>
                        """),
                        css_class='form-group col-6'
                    ),
                    css_class='form-row'
                ),
                css_class='card-footer'
            )
        )

    class Meta:
        model = Employee
        fields = [
            # General Information
            'employee_number', 'profile_picture', 'first_name', 'middle_name', 'last_name',
            'first_name_ar', 'middle_name_ar', 'last_name_ar', 'date_of_birth',
            'gender', 'marital_status', 'nationality', 'religion', 'education_category',
            'cpr_number', 'email', 'primary_phone', 'secondary_phone', 'in_probation',
            # Employment Information
            'designation', 'division', 'department', 'location', 'contract_type',
            'joined_date', 'cost_center', 'profit_center', 'employee_category',
            # System Fields
            'is_active'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'joined_date': forms.DateInput(attrs={'type': 'date'}),
        }

class EmployeeBankAccountForm(forms.ModelForm):
    class Meta:
        model = EmployeeBankAccount
        fields = ['bank', 'account_number', 'iban', 'transfer_amount', 'is_primary']
        widgets = {
            'bank': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'iban': forms.TextInput(attrs={'class': 'form-control'}),
            'transfer_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.layout = Layout(
            Row(
                Column('bank', css_class='form-group col-md-6 mb-0'),
                Column('account_number', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('iban', css_class='form-group col-md-6 mb-0'),
                Column('transfer_amount', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('is_primary', css_class='form-group col-12 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Save Bank Account', css_class='btn-primary')
        )

EmployeeBankAccountFormSet = forms.inlineformset_factory(
    Employee,
    EmployeeBankAccount,
    form=EmployeeBankAccountForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)

class EmployeeDependentForm(forms.ModelForm):
    class Meta:
        model = EmployeeDependent
        fields = [
            'name', 'relation', 'date_of_birth', 'passport_number',
            'passport_expiry', 'cpr_number', 'cpr_expiry', 'valid_passage'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'passport_expiry': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cpr_expiry': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        
        # Add Bootstrap classes to fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'

        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-0'),
                Column('relation', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('date_of_birth', css_class='form-group col-md-6 mb-0'),
                Column('valid_passage', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('passport_number', css_class='form-group col-md-6 mb-0'),
                Column('passport_expiry', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('cpr_number', css_class='form-group col-md-6 mb-0'),
                Column('cpr_expiry', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Save Dependent', css_class='btn-primary')
        )

class DependentDocumentForm(forms.ModelForm):
    class Meta:
        model = DependentDocument
        fields = ['document_type', 'document_number', 'name', 'issue_date', 'expiry_date', 'nationality', 'document_file']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['document_number'].required = False
        self.fields['issue_date'].required = False
        self.fields['expiry_date'].required = False
        self.fields['nationality'].required = False
        self.fields['document_file'].required = False
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'

        # Add Bootstrap classes to fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs['class'] = 'form-control-file'
            else:
                field.widget.attrs['class'] = 'form-control'

        self.helper.layout = Layout(
            Row(
                Column('document_type', css_class='form-group col-md-6 mb-0'),
                Column('document_number', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('name', css_class='form-group col-md-6 mb-0'),
                Column('nationality', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('issue_date', css_class='form-group col-md-6 mb-0'),
                Column('expiry_date', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('document_file', css_class='form-group col-12 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Upload Document', css_class='btn-primary')
        )

class EmergencyContactForm(forms.ModelForm):
    class Meta:
        model = EmergencyContact
        fields = ['name', 'relationship', 'phone_number', 'alternative_phone', 'address']

class EmployeeDocumentForm(forms.ModelForm):
    class Meta:
        model = EmployeeDocument
        fields = [
            'document_type', 'document_number', 'profession_title',
            'issue_date', 'issue_place', 'expiry_date', 'other_info',
            'document_file'
        ]
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'other_info': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.layout = Layout(
            Row(
                Column('document_type', css_class='form-group col-md-6 mb-0'),
                Column('document_number', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('profession_title', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('issue_date', css_class='form-group col-md-6 mb-0'),
                Column('issue_place', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('expiry_date', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('other_info', css_class='form-group col-12 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('document_file', css_class='form-group col-12 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Save Document', css_class='btn-primary')
        )

    def clean(self):
        cleaned_data = super().clean()
        issue_date = cleaned_data.get('issue_date')
        expiry_date = cleaned_data.get('expiry_date')

        if issue_date and expiry_date and expiry_date < issue_date:
            raise forms.ValidationError({
                'expiry_date': 'Expiry date cannot be earlier than issue date.'
            })

        return cleaned_data
