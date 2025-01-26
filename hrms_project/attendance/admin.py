from django.contrib import admin
from .models import (
    Shift, AttendanceRecord, AttendanceLog,
    AttendanceEdit, Leave, Holiday
)

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time', 'is_night_shift', 'is_active')
    list_filter = ('is_night_shift', 'is_active')
    search_fields = ('name',)

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'timestamp', 'device_name', 'event_point', 'is_active')
    list_filter = ('device_name', 'verify_type', 'is_active')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_number')
    date_hierarchy = 'timestamp'
    raw_id_fields = ('employee',)

@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'first_in_time', 'last_out_time', 'source', 'is_active')
    list_filter = ('source', 'is_active', 'shift')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_number')
    date_hierarchy = 'date'
    raw_id_fields = ('employee', 'created_by')

@admin.register(AttendanceEdit)
class AttendanceEditAdmin(admin.ModelAdmin):
    list_display = ('attendance_log', 'edited_by', 'edit_timestamp', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('attendance_log__employee__first_name', 'attendance_log__employee__last_name')
    date_hierarchy = 'edit_timestamp'
    raw_id_fields = ('attendance_log', 'edited_by')

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status', 'is_active')
    list_filter = ('leave_type', 'status', 'is_active')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_number')
    date_hierarchy = 'start_date'
    raw_id_fields = ('employee', 'approved_by')

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('date', 'description', 'is_paid', 'is_active')
    list_filter = ('is_paid', 'is_active')
    search_fields = ('description',)
    date_hierarchy = 'date'
    raw_id_fields = ('created_by',)