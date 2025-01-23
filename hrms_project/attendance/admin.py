from django.contrib import admin
from .models import (
    Shift, Attendance, Leave, Holiday
)

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time', 'is_night_shift', 'is_active')
    list_filter = ('is_night_shift', 'is_active')
    search_fields = ('name',)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'first_in_time', 'last_out_time', 'source', 'is_active')
    list_filter = ('source', 'is_active', 'shift')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_number')
    date_hierarchy = 'date'
    raw_id_fields = ('employee', 'created_by', 'edited_by')
    fieldsets = (
        (None, {
            'fields': ('employee', 'timestamp', 'date', 'first_in_time', 'last_out_time')
        }),
        ('Original Times', {
            'fields': ('original_first_in', 'original_last_out'),
            'classes': ('collapse',)
        }),
        ('Source Information', {
            'fields': ('device_name', 'event_point', 'verify_type', 'event_description', 'source')
        }),
        ('Edit Information', {
            'fields': ('edited_by', 'edit_timestamp', 'edit_reason')
        }),
        ('Other Information', {
            'fields': ('shift', 'is_active', 'created_by')
        })
    )

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
