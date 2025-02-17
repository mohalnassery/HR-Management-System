from django.db import models
from django.conf import settings
from employees.models import Employee
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils import timezone

class RamadanPeriod(models.Model):
    """Defines Ramadan periods for different years"""
    year = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year']
        verbose_name = 'Ramadan Period'
        verbose_name_plural = 'Ramadan Periods'

    def __str__(self):
        return f"Ramadan {self.year} ({self.start_date} to {self.end_date})"

    def clean(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError("End date cannot be before start date")
            if self.start_date.year != self.year or self.end_date.year != self.year:
                raise ValidationError("Dates must be within the specified year")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class Shift(models.Model):
    """Define different types of shifts"""
    SHIFT_TYPES = [
        ('DEFAULT', 'Default Shift'),
        ('NIGHT', 'Night Shift'),
        ('OPEN', 'Open Shift'),
    ]

    SHIFT_PRIORITIES = {
        'NIGHT': 3,    # Highest priority
        'OPEN': 2,     # Medium priority
        'DEFAULT': 1,  # Lowest priority
    }

    name = models.CharField(max_length=100)
    shift_type = models.CharField(max_length=10, choices=SHIFT_TYPES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_night_shift = models.BooleanField(default=False)
    grace_period = models.IntegerField(default=15)  # in minutes
    break_duration = models.IntegerField(default=60)  # in minutes
    is_active = models.BooleanField(default=True)
    default_night_start_time = models.TimeField(null=True, blank=True)
    default_night_end_time = models.TimeField(null=True, blank=True)
    ramadan_start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Start time during Ramadan period"
    )
    ramadan_end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="End time during Ramadan period"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def priority(self):
        """Get the priority of this shift type"""
        return self.SHIFT_PRIORITIES.get(self.shift_type, 0)

    @classmethod
    def get_default_shifts(cls):
        """Return the default shift configurations"""
        return [
            {
                'name': 'Default Shift',
                'shift_type': 'DEFAULT',
                'start_time': '07:00',
                'end_time': '16:00',
                'grace_period': 15,
                'break_duration': 60,
            },
            {
                'name': 'Night Shift',
                'shift_type': 'NIGHT',
                'start_time': '18:00',
                'end_time': '03:00',
                'grace_period': 15,
                'break_duration': 60,
            },
            {
                'name': 'Open Shift',
                'shift_type': 'OPEN',
                'start_time': '00:00',
                'end_time': '23:59',
                'grace_period': 30,
                'break_duration': 60,
            },
        ]

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['start_time']

class DateSpecificShift(models.Model):
    """Model to store date-specific shift timings"""
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='date_specific_timings')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['shift', 'date']
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.shift.name} - {self.date} ({self.start_time}-{self.end_time})"

class DateSpecificShiftOverride(models.Model):
    """Track date-specific shift time overrides"""
    date = models.DateField(unique=True, help_text="Date for which shift is overridden")
    shift_type = models.CharField(max_length=20, choices=Shift.SHIFT_TYPES, default='NIGHT', help_text="Shift type to override")
    override_start_time = models.TimeField(null=True, blank=True, help_text="Override start time")
    override_end_time = models.TimeField(null=True, blank=True, help_text="Override end time")

    def __str__(self):
        return f"{self.get_shift_type_display()} Override for {self.date}"

    class Meta:
        ordering = ['-date']
        verbose_name = 'Shift Override'
        verbose_name_plural = 'Shift Overrides'

class ShiftAssignment(models.Model):
    """Track shift assignments for employees"""
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='shift_assignments'
    )
    shift = models.ForeignKey(
        Shift,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    start_date = models.DateField(help_text="Start date of shift assignment")
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="End date of shift assignment (null = permanent)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_shift_assignments'
    )

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Shift Assignment'
        verbose_name_plural = 'Shift Assignments'

    def __str__(self):
        end = f" to {self.end_date}" if self.end_date else " (Permanent)"
        return f"{self.employee} - {self.shift.name} from {self.start_date}{end}"

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date")

        # Check for overlapping assignments
        overlapping = ShiftAssignment.objects.filter(
            employee=self.employee,
            is_active=True,
            start_date__lte=self.end_date or timezone.now().date(),
        ).exclude(pk=self.pk)

        if self.end_date:
            overlapping = overlapping.filter(
                models.Q(end_date__isnull=True) |
                models.Q(end_date__gte=self.start_date)
            )
        
        if overlapping.exists():
            raise ValidationError(
                "This assignment overlaps with an existing shift assignment"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class AttendanceRecord(models.Model):
    """Raw attendance data from machine"""
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    timestamp = models.DateTimeField()
    device_name = models.CharField(max_length=100)
    event_point = models.CharField(max_length=100)
    verify_type = models.CharField(max_length=50)
    event_description = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'timestamp']
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.employee} - {self.timestamp}"

class AttendanceLog(models.Model):
    """Processed attendance data with first in/last out times"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('leave', 'Leave'),
        ('holiday', 'Holiday')
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='attendance_logs'
    )
    date = models.DateField()
    first_in_time = models.TimeField(null=True, blank=True)
    last_out_time = models.TimeField(null=True, blank=True)
    shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='absent'
    )
    is_late = models.BooleanField(default=False)
    late_minutes = models.PositiveIntegerField(default=0)
    early_departure = models.BooleanField(default=False)
    early_minutes = models.PositiveIntegerField(default=0)
    total_work_minutes = models.PositiveIntegerField(default=0)
    source = models.CharField(
        max_length=20,
        choices=[
            ('system', 'System'),
            ('manual', 'Manual'),
            ('holiday', 'Holiday')
        ],
        default='system'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_attendance_logs'
    )

    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee} - {self.date} ({self.status})"

class AttendanceEdit(models.Model):
    """Track changes to attendance logs"""
    attendance_log = models.ForeignKey(
        AttendanceLog,
        on_delete=models.CASCADE,
        related_name='edits'
    )
    original_first_in = models.TimeField()
    original_last_out = models.TimeField()
    edited_first_in = models.TimeField()
    edited_last_out = models.TimeField()
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    edit_timestamp = models.DateTimeField(auto_now_add=True)
    edit_reason = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-edit_timestamp']

    def __str__(self):
        return f"Edit on {self.attendance_log} at {self.edit_timestamp}"

class LeaveType(models.Model):
    """Define leave types and their rules"""
    CATEGORY_CHOICES = [
        ('REGULAR', 'Regular Leave'),
        ('SPECIAL', 'Special Leave'),
        ('MEDICAL', 'Medical Leave'),
    ]
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    
    # Leave allowance configuration
    days_allowed = models.PositiveIntegerField(help_text="Number of days allowed per period")
    is_paid = models.BooleanField(default=True)
    requires_document = models.BooleanField(default=False)
    gender_specific = models.CharField(
        max_length=1, 
        choices=[('M', 'Male Only'), ('F', 'Female Only'), ('A', 'All')],
        default='A'
    )
    
    # Accrual settings
    accrual_enabled = models.BooleanField(default=False)
    accrual_days = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Days accrued per month/period"
    )
    accrual_period = models.CharField(
        max_length=10,
        choices=[('MONTHLY', 'Monthly'), ('WORKED', 'Per Worked Days')],
        null=True,
        blank=True
    )
    
    # Reset configuration
    reset_period = models.CharField(
        max_length=10,
        choices=[
            ('YEARLY', 'Yearly'),
            ('NEVER', 'Never Reset'),
            ('EVENT', 'Per Event')
        ],
        default='YEARLY'
    )
    
    # System fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        ordering = ['name']

class LeaveBalance(models.Model):
    """Track leave balances for employees"""
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leave_balances'
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name='employee_balances'
    )
    
    total_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    used_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    pending_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    last_accrual_date = models.DateField(null=True, blank=True)
    last_reset_date = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee} - {self.leave_type} Balance"
    
    @property
    def available_days(self):
        """Calculate available days excluding pending requests"""
        return self.total_days - self.used_days - self.pending_days

    class Meta:
        unique_together = ['employee', 'leave_type']
        ordering = ['employee', 'leave_type']

class LeaveBeginningBalance(models.Model):
    """Stores initial leave balances for employees as of a specific date."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='beginning_balances', verbose_name="Employee")
    leave_type = models.ForeignKey('LeaveType', on_delete=models.CASCADE, verbose_name="Leave Type")
    balance_days = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Balance Days", help_text="Initial leave balance in days.")
    as_of_date = models.DateField(help_text="Date when this balance was recorded", verbose_name="As of Date")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['employee', 'leave_type', 'as_of_date']
        verbose_name = "Leave Beginning Balance"
        verbose_name_plural = "Leave Beginning Balances"

    def __str__(self):
        return f"{self.employee} - {self.leave_type} - Balance as of {self.as_of_date}"

class LeaveRule(models.Model):
    """Defines rules and configurations for different leave types"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    days_allowed = models.DecimalField(max_digits=5, decimal_places=2)
    is_paid = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    requires_documentation = models.BooleanField(default=False)
    documentation_info = models.TextField(blank=True, help_text="What documents are required")
    reset_frequency = models.CharField(
        max_length=20,
        choices=[
            ('never', 'Never'),
            ('annually', 'Annually'),
            ('monthly', 'Monthly'),
            ('per_event', 'Per Event'),
        ],
        default='annually'
    )
    gender_specific = models.CharField(
        max_length=1,
        choices=[('M', 'Male Only'), ('F', 'Female Only'), ('A', 'All')],
        default='A'
    )
    min_service_months = models.PositiveIntegerField(default=0)
    max_days_per_request = models.PositiveIntegerField(null=True, blank=True)
    min_days_per_request = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        default=0.5
    )
    notice_days_required = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Leave(models.Model):
    """Track leave requests and their status"""
    LEAVE_STATUS = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leaves'
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name='leave_requests'
    )
    
    # Request details
    start_date = models.DateField()
    end_date = models.DateField()
    duration = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="Duration in days"
    )
    start_half = models.BooleanField(
        default=False,
        help_text="True if starting with half day"
    )
    end_half = models.BooleanField(
        default=False,
        help_text="True if ending with half day"
    )
    reason = models.TextField()
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=LEAVE_STATUS,
        default='draft'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_leaves'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    # System fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.start_date} to {self.end_date})"

    def clean(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError("End date cannot be before start date")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class LeaveDocument(models.Model):
    """Store documents related to leave requests"""
    leave = models.ForeignKey(
        Leave,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document = models.FileField(
        upload_to='leave_documents/%Y/%m/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png']
            )
        ]
    )
    document_type = models.CharField(max_length=50)
    notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.leave} - {self.document_type}"

class LeaveActivity(models.Model):
    """Track all activities related to leave requests"""
    leave = models.ForeignKey(
        Leave,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    action = models.CharField(max_length=50)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.leave} - {self.action} by {self.actor}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Leave activities'

class Holiday(models.Model):
    """Define holidays and their configurations"""
    HOLIDAY_TYPES = [
        ('PUBLIC', 'Public Holiday'),
        ('COMPANY', 'Company Holiday'),
        ('OPTIONAL', 'Optional Holiday')
    ]
    
    name = models.CharField(max_length=100)
    date = models.DateField()
    holiday_type = models.CharField(
        max_length=20,
        choices=HOLIDAY_TYPES,
        default='PUBLIC'
    )
    is_recurring = models.BooleanField(
        default=False,
        help_text="If True, holiday repeats every year"
    )
    description = models.TextField(blank=True)
    is_paid = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.name} ({self.date})"
