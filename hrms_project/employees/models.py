from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import FileExtensionValidator
import os

class Department(models.Model):
    name = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100, verbose_name="Name (Arabic)", blank=True, null=True)
    code = models.CharField(max_length=20, default='DEPT', unique=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.name

class Division(models.Model):
    name = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100, verbose_name="Name (Arabic)")
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

class Bank(models.Model):
    name = models.CharField(max_length=100)
    swift_code = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class Employee(models.Model):
    # Choice Fields
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    MARITAL_STATUS_CHOICES = [
        ('S', 'Single'),
        ('M', 'Married'),
        ('D', 'Divorced'),
        ('W', 'Widowed'),
    ]
    CONTRACT_TYPE_CHOICES = [
        ('FT', 'Full Time'),
        ('PT', 'Part Time'),
        ('CT', 'Contract'),
        ('INT', 'Intern'),
    ]
    EMPLOYEE_CATEGORY_CHOICES = [
        ('STF', 'Staff'),
        ('WRK', 'Worker'),
        ('MGR', 'Manager'),
        ('EXE', 'Executive'),
    ]

    # General Information
    employee_number = models.CharField(max_length=20, unique=True, default='EMP0001')
    first_name = models.CharField(max_length=50, default='First')
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, default='Last')
    first_name_ar = models.CharField(max_length=50, verbose_name="First Name (Arabic)", blank=True, null=True)
    middle_name_ar = models.CharField(max_length=50, verbose_name="Middle Name (Arabic)", blank=True, null=True)
    last_name_ar = models.CharField(max_length=50, verbose_name="Last Name (Arabic)", blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True, null=True)
    nationality = models.CharField(max_length=50, blank=True, null=True)
    religion = models.CharField(max_length=50, blank=True, null=True)
    education_category = models.CharField(max_length=50, blank=True, null=True)
    cpr_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)

    # Employment Information
    designation = models.CharField(max_length=100, blank=True, null=True)
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES, blank=True, null=True)
    joined_date = models.DateField(blank=True, null=True)
    rejoined_date = models.DateField(blank=True, null=True)
    in_probation = models.BooleanField(default=True)
    is_manager = models.BooleanField(default=False)
    cost_center = models.CharField(max_length=50, blank=True, null=True)
    profit_center = models.CharField(max_length=50, blank=True, null=True)
    employee_category = models.CharField(max_length=20, choices=EMPLOYEE_CATEGORY_CHOICES, blank=True, null=True)
    payroll_group = models.CharField(max_length=50, blank=True, null=True)

    # Visa & Accommodation
    company_accommodation = models.BooleanField(default=False)
    visa_cr_number = models.CharField(max_length=50, blank=True, null=True)
    sponsor_name = models.CharField(max_length=100, blank=True, null=True)
    accom_occu_date = models.DateField(verbose_name="Accommodation Occupation Date", blank=True, null=True)

    # Contract Details
    contract_start_date = models.DateField(blank=True, null=True)
    contract_end_date = models.DateField(blank=True, null=True)
    notice_period = models.IntegerField(default=30, help_text="Notice period in days")
    leave_accrual_rate = models.DecimalField(max_digits=4, decimal_places=2, default=2.5)

    # Salary Information
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Bond Details
    bond_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    guarantee_details = models.TextField(blank=True, null=True)

    # System Fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        ordering = ['employee_number']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_number})"

    def get_full_name(self):
        middle = f" {self.middle_name}" if self.middle_name else ""
        return f"{self.first_name}{middle} {self.last_name}"

    def get_full_name_ar(self):
        middle = f" {self.middle_name_ar}" if self.middle_name_ar else ""
        return f"{self.first_name_ar}{middle} {self.last_name_ar}"

class EmployeeBankAccount(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='bank_accounts')
    bank = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    iban = models.CharField(max_length=50, verbose_name="IBAN No")
    transfer_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Amount to be Transferred",
        null=True,
        blank=True
    )
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_primary', '-created_at']
        verbose_name = "Employee Bank Account"
        verbose_name_plural = "Employee Bank Accounts"

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.bank} ({self.account_number})"

    def save(self, *args, **kwargs):
        # If this account is being set as primary, unset primary for other accounts
        if self.is_primary:
            EmployeeBankAccount.objects.filter(
                employee=self.employee, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

class EmployeeDependent(models.Model):
    RELATIONSHIP_CHOICES = [
        ('SP', 'Spouse'),
        ('CH', 'Child'),
        ('PR', 'Parent'),
        ('SB', 'Sibling'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='dependents')
    name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=2, choices=RELATIONSHIP_CHOICES)
    date_of_birth = models.DateField()
    is_sponsored = models.BooleanField(default=False)
    documents = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.name} ({self.get_relationship_display()})"

class EmergencyContact(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=20)
    alternative_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.relationship})"

class EmployeeDocument(models.Model):
    DOCUMENT_TYPES = [
        ('PASSPORT', 'Passport'),
        ('RESIDENT', 'Resident Permit'),
        ('CPR', 'C.P.R'),
        ('GATE', 'Gate Pass'),
        ('CONTRACT', 'Contract'),
        ('CV', 'CV'),
        ('DRIVING', 'Driving License'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES)
    document_number = models.CharField(max_length=50)
    profession_title = models.CharField(max_length=100, blank=True, null=True, verbose_name="Profession / Title")
    issue_date = models.DateField(null=True, blank=True)
    issue_place = models.CharField(max_length=100, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    other_info = models.TextField(blank=True, null=True)
    document_file = models.FileField(
        upload_to='employee_documents/%Y/%m/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
            )
        ],
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Employee Document"
        verbose_name_plural = "Employee Documents"

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_document_type_display()}"

    def clean(self):
        if self.expiry_date and self.issue_date:
            if self.expiry_date < self.issue_date:
                raise ValidationError({
                    'expiry_date': 'Expiry date cannot be earlier than issue date.'
                })

    def save(self, *args, **kwargs):
        if not self.pk:  # Only set created_at for new instances
            self.created_at = timezone.now()
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return self.expiry_date < timezone.now().date() if self.expiry_date else False

    @property
    def file_extension(self):
        name, extension = os.path.splitext(self.document_file.name)
        return extension.lower()

    @property
    def is_image(self):
        return self.file_extension in ['.jpg', '.jpeg', '.png']

class EmployeeAsset(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='assets')
    asset_name = models.CharField(max_length=100)
    asset_number = models.CharField(max_length=50)
    issue_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    condition = models.TextField()
    value = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.asset_name} ({self.asset_number})"

class EmployeeEducation(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='education')
    institution = models.CharField(max_length=100, default='Unknown Institution')
    major = models.CharField(max_length=100, default='General')
    degree = models.CharField(max_length=50, default='Unknown Degree')
    graduation_year = models.IntegerField(default=2000)
    gpa = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.degree} from {self.institution}"

class EmployeeOffence(models.Model):
    SEVERITY_CHOICES = [
        ('L', 'Low'),
        ('M', 'Medium'),
        ('H', 'High'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='offences')
    date = models.DateField()
    description = models.TextField()
    severity = models.CharField(max_length=1, choices=SEVERITY_CHOICES)
    action_taken = models.TextField()
    warning_letter = models.FileField(upload_to='warning_letters/', blank=True)

    def __str__(self):
        return f"{self.get_severity_display()} severity offence on {self.date}"

class LifeEvent(models.Model):
    EVENT_TYPES = [
        ('MAR', 'Marriage'),
        ('CHD', 'Child Birth'),
        ('DEA', 'Death in Family'),
        ('OTH', 'Other'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='life_events')
    event_type = models.CharField(max_length=3, choices=EVENT_TYPES)
    date = models.DateField()
    description = models.TextField()
    documents = models.FileField(upload_to='life_event_documents/', blank=True)

    def __str__(self):
        return f"{self.get_event_type_display()} on {self.date}"
