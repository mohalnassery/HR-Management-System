from django.db import models
from django.conf import settings
from employees.models import Employee
from django.core.exceptions import ValidationError
from django.utils import timezone

class Shift(models.Model):
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_night_shift = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.start_time}-{self.end_time})"

    class Meta:
        ordering = ['start_time']

class Attendance(models.Model):
    """Combined attendance record with edit history"""
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='attendance'
    )
    # Date & Time from the source (machine or manual entry)
    timestamp = models.DateTimeField()
    date = models.DateField() 
    
    # Clock in/out times
    first_in_time = models.TimeField()
    last_out_time = models.TimeField()
    
    # Original times (for edit history)
    original_first_in = models.TimeField()
    original_last_out = models.TimeField()
    
    # Source information
    device_name = models.CharField(max_length=100, blank=True, null=True)
    event_point = models.CharField(max_length=100, blank=True, null=True)
    verify_type = models.CharField(max_length=50, blank=True, null=True)
    event_description = models.TextField(blank=True, null=True)
    source = models.CharField(
        max_length=20,
        choices=[('system', 'System'), ('manual', 'Manual'), ('machine', 'Machine')],
        default='machine'
    )

    # Edit information
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='edited_attendance'
    )
    edit_timestamp = models.DateTimeField(null=True, blank=True)
    edit_reason = models.TextField(blank=True, null=True)

    # Shift information
    shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Status and tracking
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_attendance'
    )

    class Meta:
        unique_together = ['employee', 'timestamp']
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.employee} - {self.timestamp}"

    def save(self, *args, **kwargs):
        # When first created, set original times
        if not self.pk:  
            self.original_first_in = self.first_in_time
            self.original_last_out = self.last_out_time
        
        # Set the date field from timestamp
        if self.timestamp:
            self.date = self.timestamp.date()
            
        super().save(*args, **kwargs)

class Leave(models.Model):
    LEAVE_TYPES = [
        ('annual', 'Annual Leave'),
        ('sick', 'Sick Leave'),
        ('permission', 'Permission')
    ]
    LEAVE_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leaves'
    )
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=LEAVE_STATUS,
        default='pending'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_leaves'
    )
    remarks = models.TextField(blank=True, null=True)
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

class Holiday(models.Model):
    date = models.DateField(unique=True)
    description = models.CharField(max_length=200)
    is_paid = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.description}"
