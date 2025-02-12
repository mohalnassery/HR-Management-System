from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Shift, ShiftAssignment, RamadanPeriod, AttendanceRecord, 
    AttendanceLog, Leave, LeaveType, Holiday, DateSpecificShiftOverride
)

@admin.register(DateSpecificShiftOverride)
class DateSpecificShiftOverrideAdmin(admin.ModelAdmin):
    list_display = ('date', 'shift_type', 'override_start_time', 'override_end_time')
    list_filter = ('shift_type',)
    date_hierarchy = 'date'
    search_fields = ('date',)

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'shift_type_display', 'timing_display', 'default_timing_display', 'break_display', 'is_active')
    list_filter = ('shift_type', 'is_active')
    search_fields = ('name', 'description')
    ordering = ('shift_type', 'name')
    
    def shift_type_display(self, obj):
        shift_colors = {
            'DEFAULT': 'green',
            'NIGHT': 'purple',
            'OPEN': 'blue'
        }
        color = shift_colors.get(obj.shift_type, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_shift_type_display()
        )
    shift_type_display.short_description = 'Type'
    
    def timing_display(self, obj):
        return format_html(
            '<span title="Current shift timing">{}</span>',
            f"{obj.start_time.strftime('%I:%M %p')} - {obj.end_time.strftime('%I:%M %p')}"
        )
    timing_display.short_description = 'Current Timing'
    
    def default_timing_display(self, obj):
        if obj.default_start_time and obj.default_end_time:
            return format_html(
                '<span title="Default shift timing">{}</span>',
                f"{obj.default_start_time.strftime('%I:%M %p')} - {obj.default_end_time.strftime('%I:%M %p')}"
            )
        return format_html('<span class="text-muted">Not set</span>')
    default_timing_display.short_description = 'Default Timing'

    def break_display(self, obj):
        return format_html(
            '<span title="Break duration & Grace period">{}m break / {}m grace</span>',
            obj.break_duration,
            obj.grace_period
        )
    break_display.short_description = 'Break/Grace'

@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ('employee_link', 'shift_link', 'period_display', 'is_active', 'created_by', 'created_at')
    list_filter = ('is_active', 'shift', 'created_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_number', 'shift__name')
    ordering = ('-created_at',)
    raw_id_fields = ('employee', 'shift')
    
    def employee_link(self, obj):
        url = reverse('admin:employees_employee_change', args=[obj.employee.id])
        return format_html('<a href="{}">{}</a>', url, obj.employee)
    employee_link.short_description = 'Employee'
    
    def shift_link(self, obj):
        url = reverse('admin:attendance_shift_change', args=[obj.shift.id])
        return format_html('<a href="{}">{}</a>', url, obj.shift.name)
    shift_link.short_description = 'Shift'
    
    def period_display(self, obj):
        if obj.end_date:
            return f"{obj.start_date.strftime('%b %d, %Y')} - {obj.end_date.strftime('%b %d, %Y')}"
        return f"From {obj.start_date.strftime('%b %d, %Y')} (Permanent)"
    period_display.short_description = 'Period'

@admin.register(RamadanPeriod)
class RamadanPeriodAdmin(admin.ModelAdmin):
    list_display = ('year', 'start_date', 'end_date', 'duration_display', 'is_active')
    list_filter = ('year', 'is_active')
    search_fields = ('year',)
    ordering = ('-year',)
    
    def duration_display(self, obj):
        if obj.start_date and obj.end_date:
            duration = (obj.end_date - obj.start_date).days + 1
            return f"{duration} days"
        return "Not set"
    duration_display.short_description = 'Duration'

@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ('employee_link', 'date', 'time_display', 'status_display', 'source')
    list_filter = ('date', 'source', 'status', 'is_active')  
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_number')
    date_hierarchy = 'date'
    ordering = ('-date', 'employee__first_name')
    raw_id_fields = ('employee',)

    def employee_link(self, obj):
        url = reverse('admin:employees_employee_change', args=[obj.employee.id])
        return format_html('<a href="{}">{}</a>', url, obj.employee)
    employee_link.short_description = 'Employee'

    def time_display(self, obj):
        if obj.first_in_time and obj.last_out_time:
            return f"{obj.first_in_time.strftime('%I:%M %p')} - {obj.last_out_time.strftime('%I:%M %p')}"
        return "No time records"
    time_display.short_description = 'Timing'

    def status_display(self, obj):
        status_colors = {
            'present': 'green',
            'absent': 'red',
            'late': 'orange',
            'leave': 'blue',
            'holiday': 'purple'
        }
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('employee_link', 'timestamp', 'event_point', 'device_name')  
    list_filter = ('event_point', 'timestamp')  
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_number', 'device_name')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    raw_id_fields = ('employee',)

    def employee_link(self, obj):
        url = reverse('admin:employees_employee_change', args=[obj.employee.id])
        return format_html('<a href="{}">{}</a>', url, obj.employee)
    employee_link.short_description = 'Employee'

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('employee_link', 'leave_type', 'period_display', 'duration', 'status', 'created_at')  
    list_filter = ('status', 'leave_type', 'created_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_number')
    date_hierarchy = 'start_date'
    ordering = ('-created_at',)
    raw_id_fields = ('employee',)

    def employee_link(self, obj):
        url = reverse('admin:employees_employee_change', args=[obj.employee.id])
        return format_html('<a href="{}">{}</a>', url, obj.employee)
    employee_link.short_description = 'Employee'

    def period_display(self, obj):
        return f"{obj.start_date.strftime('%b %d, %Y')} - {obj.end_date.strftime('%b %d, %Y')}"
    period_display.short_description = 'Period'

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'days_allowed', 'is_paid', 'is_active')
    list_filter = ('is_paid', 'is_active')
    search_fields = ('name', 'code')
    ordering = ('name',)

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'is_recurring', 'is_active')
    list_filter = ('is_recurring', 'is_active')
    search_fields = ('name',)
    date_hierarchy = 'date'
    ordering = ('-date',)
