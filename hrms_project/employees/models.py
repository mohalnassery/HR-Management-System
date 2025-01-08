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

class CostProfitCenter(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = 'Cost/Profit Center'
        verbose_name_plural = 'Cost/Profit Centers'
        ordering = ['code']

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
        ('GEN', 'General'),
        ('SUP', 'Supervisor'),
        ('MGR', 'Manager'),
        ('EXE', 'Executive'),
    ]
    NATIONALITY_CHOICES = [
        ('ALGERIAN', 'Algerian'),
        ('AMERICAN', 'American'),
        ('ARGENTINA', 'Argentina'),
        ('AUSTRALIAN', 'Australian'),
        ('BAHRAINI', 'Bahraini'),
        ('BANGLADESHI', 'Bangladeshi'),
        ('BELGIAN', 'Belgian'),
        ('BRAZILIAN', 'Brazilian'),
        ('BRITISH', 'British'),
        ('BULGARIAN', 'Bulgarian'),
        ('CAMEROONIAN', 'Cameroonian'),
        ('CANADIAN', 'Canadian'),
        ('CHILEAN', 'Chilean'),
        ('CHINESE', 'Chinese'),
        ('COLOMBIAN', 'Colombian'),
        ('CROATIAN', 'Croatian'),
        ('CUBAN', 'Cuban'),
        ('CYPRIOT', 'Cypriot'),
        ('CZECH', 'Czech'),
        ('DANISH', 'Danish'),
        ('DJIBOUTIAN', 'Djiboutian'),
        ('EGYPTIAN', 'Egyptian'),
        ('FILIPINO', 'Filipino'),
        ('FRENCH', 'French'),
        ('GERMAN', 'German'),
        ('GHANAIAN', 'Ghanaian'),
        ('GREEK', 'Greek'),
        ('DUTCH', 'Dutch'),
        ('HONG_KONGER', 'Hong Konger'),
        ('INDIAN', 'Indian'),
        ('INDONESIAN', 'Indonesian'),
        ('IRANIAN', 'Iranian'),
        ('IRAQI', 'Iraqi'),
        ('IRISH', 'Irish'),
        ('ITALIAN', 'Italian'),
        ('JAMAICAN', 'Jamaican'),
        ('JAPANESE', 'Japanese'),
        ('JORDANIAN', 'Jordanian'),
        ('KENYAN', 'Kenyan'),
        ('KUWAITI', 'Kuwaiti'),
        ('LEBANESE', 'Lebanese'),
        ('MALAWIAN', 'Malawian'),
        ('MALAYSIAN', 'Malaysian'),
        ('MEXICAN', 'Mexican'),
        ('MOROCCAN', 'Moroccan'),
        ('NEPALI', 'Nepali'),
        ('DUTCH', 'Dutch'),
        ('NEW_ZEALANDER', 'New Zealander'),
        ('NIGERIAN', 'Nigerian'),
        ('NORWEGIAN', 'Norwegian'),
        ('OMANI', 'Omani'),
        ('PAKISTANI', 'Pakistani'),
        ('POLISH', 'Polish'),
        ('PORTUGUESE', 'Portuguese'),
        ('RUSSIAN', 'Russian'),
        ('SAUDI', 'Saudi'),
        ('SCOTTISH', 'Scottish'),
        ('SERBIAN', 'Serbian'),
        ('SEYCHELLOIS', 'Seychellois'),
        ('SINGAPOREAN', 'Singaporean'),
        ('SOUTH_AFRICAN', 'South African'),
        ('SPANISH', 'Spanish'),
        ('SRI_LANKAN', 'Sri Lankan'),
        ('SUDANESE', 'Sudanese'),
        ('SWEDISH', 'Swedish'),
        ('SWISS', 'Swiss'),
        ('SYRIAN', 'Syrian'),
        ('TAIWANESE', 'Taiwanese'),
        ('TANZANIAN', 'Tanzanian'),
        ('THAI', 'Thai'),
        ('TUNISIAN', 'Tunisian'),
        ('TURKISH', 'Turkish'),
        ('EMIRATI', 'Emirati'),
        ('UGANDAN', 'Ugandan'),
        ('UKRAINIAN', 'Ukrainian'),
        ('VENEZUELAN', 'Venezuelan'),
        ('VIETNAMESE', 'Vietnamese'),
        ('YEMENI', 'Yemeni'),
        ('ZIMBABWEAN', 'Zimbabwean'),
        ('OTHER', 'Other'),
    ]

    # General Information
    employee_number = models.CharField(max_length=20, unique=True, default='EMP0001')
    profile_picture = models.ImageField(upload_to='employee_pictures/', blank=True, null=True)
    first_name = models.CharField(max_length=50, default='First')
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, default='Last')
    first_name_ar = models.CharField(max_length=50, verbose_name="First Name (Arabic)", blank=True, null=True)
    middle_name_ar = models.CharField(max_length=50, verbose_name="Middle Name (Arabic)", blank=True, null=True)
    last_name_ar = models.CharField(max_length=50, verbose_name="Last Name (Arabic)", blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True, null=True)
    nationality = models.CharField(
        max_length=50,
        choices=NATIONALITY_CHOICES,
        blank=True,
        null=True,
        verbose_name='Nationality'
    )
    religion = models.CharField(max_length=50, blank=True, null=True)
    education_category = models.CharField(max_length=50, blank=True, null=True)
    cpr_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)
    primary_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Primary Number')
    secondary_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Secondary Number')
    address = models.TextField(blank=True, null=True)
    in_probation = models.BooleanField(default=True)

    # Employment Information
    designation = models.CharField(max_length=100, blank=True, null=True)
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES, blank=True, null=True)
    joined_date = models.DateField(blank=True, null=True)
    cost_center = models.ForeignKey(CostProfitCenter, on_delete=models.SET_NULL, null=True, blank=True, related_name='cost_center_employees')
    profit_center = models.ForeignKey(CostProfitCenter, on_delete=models.SET_NULL, null=True, blank=True, related_name='profit_center_employees')
    employee_category = models.CharField(max_length=20, choices=EMPLOYEE_CATEGORY_CHOICES, blank=True, null=True)

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
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
        ('other', 'Other'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='dependents')
    name = models.CharField(max_length=100)
    relation = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    date_of_birth = models.DateField()
    passport_number = models.CharField(max_length=50, blank=True, null=True)
    passport_expiry = models.DateField(blank=True, null=True)
    cpr_number = models.CharField(max_length=20, blank=True, null=True)
    cpr_expiry = models.DateField(blank=True, null=True)
    valid_passage = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Employee Dependent"
        verbose_name_plural = "Employee Dependents"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_relation_display()})"

class DependentDocument(models.Model):
    DOCUMENT_TYPES = [
        ('PASSPORT', 'Passport'),
        ('CPR', 'CPR'),
        ('BIRTH_CERTIFICATE', 'Birth Certificate'),
        ('MARRIAGE_CERTIFICATE', 'Marriage Certificate'),
        ('OTHER', 'Other'),
    ]

    dependent = models.ForeignKey(EmployeeDependent, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    document_number = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=255)
    issue_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    nationality = models.CharField(max_length=50, choices=Employee.NATIONALITY_CHOICES, blank=True, null=True)
    document_file = models.FileField(upload_to='dependent_documents/', blank=True, null=True)
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.dependent.name} - {self.get_document_type_display()}"

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
            
        if self.document_file:
            # Get file extension
            _, ext = os.path.splitext(self.document_file.name)
            
            # Create new filename
            new_filename = f"{self.employee.employee_number}_{self.employee.get_full_name().replace(' ', '_')}_{self.get_document_type_display()}_{self.document_number}{ext}"
            
            # Set the new filename
            self.document_file.name = os.path.join(
                'employee_documents',
                timezone.now().strftime('%Y'),
                timezone.now().strftime('%m'),
                new_filename
            )
            
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
