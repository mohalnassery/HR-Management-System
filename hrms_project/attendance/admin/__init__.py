from django.contrib import admin

from .base import (
    BaseModelAdmin,
    EmployeeLinkedModelAdmin,
    PeriodModelAdmin,
    ColorCodedStatusMixin
)
from ..models import (
    Shift, ShiftAssignment, RamadanPeriod, AttendanceRecord, 
    AttendanceLog, Leave, LeaveType, Holiday, DateSpecificShiftOverride
)
from ..utils.display import DisplayFormatter, SHIFT_TYPE_COLORS, STATUS_COLORS

@admin.register(DateSpecificShiftOverride)
class DateSpecificShiftOverrideAdmin(BaseModelAdmin):
    list_display = ('date', 'shift_type', 'override_start_time', 'override_end_time')
    list_filter = ('shift_type',)
    date_hierarchy = 'date'
    search_fields = ('date',)

@admin.register(Shift)
class ShiftAdmin(BaseModelAdmin):
    list_display = ('name', 'shift_type_display', 'timing_display', 'default_timing_display', 'break_display', 'is_active')
    list_filter = ('shift_type', 'is_active')
    search_fields = ('name', 'description')
    ordering = ('shift_type', 'name')
    
    def shift_type_display(self, obj):
        return DisplayFormatter.color_coded_display(
            obj.shift_type,
            obj.get_shift_type_display(),
            SHIFT_TYPE_COLORS
        )
    shift_type_display.short_description = 'Type'
    
    def timing_display(self, obj):
        return DisplayFormatter.timing_display(
            obj.start_time,
            obj.end_time,
            "Current shift timing"
        )
    timing_display.short_description = 'Current Timing'
    
    def default_timing_display(self, obj):
        return DisplayFormatter.timing_display(
            obj.default_start_time,
            obj.default_end_time,
            "Default shift timing"
        )
    default_timing_display.short_description = 'Default Timing'

    def break_display(self, obj):
        return format_html(
            '<span title="Break duration & Grace period">{}m break / {}m grace</span>',
            obj.break_duration,
            obj.grace_period
        )
    break_display.short_description = 'Break/Grace'

@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(EmployeeLinkedModelAdmin, PeriodModelAdmin):
    list_display = ('employee_link', 'shift_link', 'period_display', 'is_active', 'created_by', 'created_at')
    list_filter = ('is_active', 'shift', 'created_at')
    raw_id_fields = ('employee', 'shift')
    
    def shift_link(self, obj):
        url = reverse('admin:attendance_shift_change', args=[obj.shift.id])
        return format_html('<a href="{}">{}</a>', url, obj.shift.name)
    shift_link.short_description = 'Shift'

@admin.register(RamadanPeriod)
class RamadanPeriodAdmin(PeriodModelAdmin):
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
class AttendanceLogAdmin(EmployeeLinkedModelAdmin, ColorCodedStatusMixin):
    list_display = ('employee_link', 'date', 'time_display', 'status_display', 'source')
    list_filter = ('date', 'source', 'status', 'is_active')  
    date_hierarchy = 'date'
    ordering = ('-date', 'employee__first_name')
    raw_id_fields = ('employee',)

    def time_display(self, obj):
        return DisplayFormatter.timing_display(
            obj.first_in_time,
            obj.last_out_time
        )
    time_display.short_description = 'Timing'

    status_colors = STATUS_COLORS

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(EmployeeLinkedModelAdmin):
    list_display = ('employee_link', 'timestamp', 'event_point', 'device_name')  
    list_filter = ('event_point', 'timestamp')  
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    raw_id_fields = ('employee',)

@admin.register(Leave)
class LeaveAdmin(EmployeeLinkedModelAdmin, PeriodModelAdmin, ColorCodedStatusMixin):
    list_display = ('employee_link', 'leave_type', 'period_display', 'duration', 'status_display', 'created_at')  
    list_filter = ('status', 'leave_type', 'created_at')
    date_hierarchy = 'start_date'
    raw_id_fields = ('employee',)

    status_colors = {
        'pending': 'orange',
        'approved': 'green',
        'rejected': 'red',
        'cancelled': 'gray'
    }

@admin.register(LeaveType)
class LeaveTypeAdmin(BaseModelAdmin):
    list_display = ('name', 'code', 'days_allowed', 'is_paid', 'is_active')
    list_filter = ('is_paid', 'is_active')
    search_fields = ('name', 'code')
    ordering = ('name',)

@admin.register(Holiday)
class HolidayAdmin(BaseModelAdmin):
    list_display = ('name', 'date', 'is_recurring', 'is_active')
    list_filter = ('is_recurring', 'is_active')
    search_fields = ('name',)
    date_hierarchy = 'date'
    ordering = ('-date',)
