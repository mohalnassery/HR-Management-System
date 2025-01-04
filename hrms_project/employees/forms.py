from django import forms
from django.db import transaction
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from .models import Employee, Department, Division, EmployeeDependent, EmergencyContact, EmployeeDocument, EmployeeBankAccount

class EmployeeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        
        # Make some fields optional
        optional_fields = ['middle_name', 'middle_name_ar', 'religion',
                         'education_category', 'rejoined_date', 'bond_amount',
                         'guarantee_details', 'visa_cr_number', 'sponsor_name',
                         'accom_occu_date', 'contract_end_date']
        
        for field in optional_fields:
            self.fields[field].required = False

        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': field.label
                })
            else:
                field.widget.attrs.update({
                    'class': 'form-check-input'
                })

        # Filter manager choices to only active employees
        manager_qs = Employee.objects.filter(is_active=True)
        if self.instance.pk:
            manager_qs = manager_qs.exclude(pk=self.instance.pk)
        self.fields['manager'].queryset = manager_qs.select_related('department')

        # Load related fields efficiently
        self.fields['department'].queryset = Department.objects.all().select_related('manager')
        self.fields['division'].queryset = Division.objects.all().select_related('department')

        self.helper.layout = Layout(
            Row(
                Column('employee_number', css_class='form-group col-md-6 mb-0'),
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('middle_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('first_name_ar', css_class='form-group col-md-6 mb-0'),
                Column('middle_name_ar', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('last_name_ar', css_class='form-group col-md-6 mb-0'),
                Column('date_of_birth', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('gender', css_class='form-group col-md-6 mb-0'),
                Column('marital_status', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('nationality', css_class='form-group col-md-6 mb-0'),
                Column('religion', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('education_category', css_class='form-group col-md-6 mb-0'),
                Column('cpr_number', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('profession_cpr', css_class='form-group col-md-6 mb-0'),
                Column('email', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('designation', css_class='form-group col-md-6 mb-0'),
                Column('division', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('department', css_class='form-group col-md-6 mb-0'),
                Column('manager', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('location', css_class='form-group col-md-6 mb-0'),
                Column('contract_type', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('joined_date', css_class='form-group col-md-6 mb-0'),
                Column('rejoined_date', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('in_probation', css_class='form-group col-md-6 mb-0'),
                Column('is_manager', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('cost_center', css_class='form-group col-md-6 mb-0'),
                Column('profit_center', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('employee_category', css_class='form-group col-md-6 mb-0'),
                Column('payroll_group', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('company_accommodation', css_class='form-group col-md-6 mb-0'),
                Column('visa_cr_number', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('sponsor_name', css_class='form-group col-md-6 mb-0'),
                Column('accom_occu_date', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('bank', css_class='form-group col-md-6 mb-0'),
                Column('account_number', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('iban', css_class='form-group col-md-6 mb-0'),
                Column('contract_start_date', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('contract_end_date', css_class='form-group col-md-6 mb-0'),
                Column('notice_period', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('leave_accrual_rate', css_class='form-group col-md-6 mb-0'),
                Column('basic_salary', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('total_allowances', css_class='form-group col-md-6 mb-0'),
                Column('total_deductions', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('bond_amount', css_class='form-group col-md-6 mb-0'),
                Column('guarantee_details', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('is_active', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Submit')
        )

    class Meta:
        model = Employee
        fields = [
            # General Information
            'employee_number', 'first_name', 'middle_name', 'last_name',
            'first_name_ar', 'middle_name_ar', 'last_name_ar',
            'date_of_birth', 'gender', 'marital_status', 'nationality',
            'religion', 'education_category', 'cpr_number', 'profession_cpr',
            'email',
            
            # Employment Information
            'designation', 'division', 'department', 'manager',
            'location', 'contract_type', 'joined_date', 'rejoined_date',
            'in_probation', 'is_manager', 'cost_center', 'profit_center',
            'employee_category', 'payroll_group',
            
            # Visa & Accommodation
            'company_accommodation', 'visa_cr_number', 'sponsor_name',
            'accom_occu_date',
            
            # Contract Details
            'contract_start_date', 'contract_end_date', 'notice_period',
            'leave_accrual_rate',
            
            # Salary Information
            'basic_salary', 'total_allowances', 'total_deductions',
            
            # Bond Details
            'bond_amount', 'guarantee_details',
            
            # System Fields
            'is_active'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'joined_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'rejoined_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'contract_start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'contract_end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'accom_occu_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        
        # Validate dates
        joined_date = cleaned_data.get('joined_date')
        contract_start_date = cleaned_data.get('contract_start_date')
        contract_end_date = cleaned_data.get('contract_end_date')
        
        if joined_date and contract_start_date and joined_date != contract_start_date:
            self.add_error('contract_start_date', 'Contract start date should match joined date')
        
        if contract_start_date and contract_end_date and contract_end_date <= contract_start_date:
            self.add_error('contract_end_date', 'Contract end date must be after start date')
        
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        employee = super().save(commit=False)
        if commit:
            employee.save()
        return employee

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
        fields = ['name', 'relationship', 'date_of_birth', 'is_sponsored']

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
