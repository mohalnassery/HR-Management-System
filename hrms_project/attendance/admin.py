from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Shift, AttendanceRecord, AttendanceLog,
    AttendanceEdit, LeaveType, LeaveBalance, 
    Leave, LeaveDocument, LeaveActivity, Holiday
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

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'days_allowed', 'is_paid', 'accrual_enabled', 'is_active')
    list_filter = ('category', 'is_paid', 'requires_document', 'reset_period', 'is_active')
    search_fields = ('name', 'code', 'description')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'category', 'description')
        }),
        ('Leave Configuration', {
            'fields': ('days_allowed', 'is_paid', 'requires_document', 'gender_specific')
        }),
        ('Accrual Settings', {
            'fields': ('accrual_enabled', 'accrual_days', 'accrual_period', 'reset_period')
        }),
        ('System', {
            'fields': ('is_active',),
            'classes': ('collapse',)
        })
    )

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'total_days', 'used_days', 'pending_days', 'available_days', 'valid_until')
    list_filter = ('leave_type', 'is_active')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_number')
    raw_id_fields = ('employee',)
    readonly_fields = ('available_days',)
    
    def available_days(self, obj):
        days = obj.available_days
        color = 'green' if days > 5 else 'orange' if days > 0 else 'red'
        return format_html('<span style="color: {};">{}</span>', color, days)
    available_days.short_description = 'Available'

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'duration', 'status', 'is_active')
    list_filter = ('leave_type', 'status', 'is_active', 'start_date')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_number')
    date_hierarchy = 'start_date'
    raw_id_fields = ('employee', 'approved_by')
    readonly_fields = ('submitted_at', 'approved_at')
    
    fieldsets = (
        ('Request Information', {
            'fields': (
                'employee', 'leave_type', 'start_date', 'end_date',
                'duration', 'start_half', 'end_half', 'reason'
            )
        }),
        ('Status', {
            'fields': (
                'status', 'submitted_at', 'approved_by', 'approved_at',
                'rejection_reason', 'cancellation_reason'
            )
        }),
        ('System', {
            'fields': ('is_active',),
            'classes': ('collapse',)
        })
    )

@admin.register(LeaveDocument)
class LeaveDocumentAdmin(admin.ModelAdmin):
    list_display = ('leave', 'document_type', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('leave__employee__first_name', 'leave__employee__last_name')
    date_hierarchy = 'uploaded_at'

@admin.register(LeaveActivity)
class LeaveActivityAdmin(admin.ModelAdmin):
    list_display = ('leave', 'action', 'actor', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('leave__employee__first_name', 'leave__employee__last_name', 'details')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'holiday_type', 'is_recurring', 'is_paid', 'is_active')
    list_filter = ('holiday_type', 'is_recurring', 'is_paid', 'is_active')
    search_fields = ('name', 'description')
    filter_horizontal = ('applicable_departments',)
    date_hierarchy = 'date'
    raw_id_fields = ('created_by',)
    
    fieldsets = (
        ('Holiday Information', {
            'fields': ('name', 'date', 'holiday_type', 'description')
        }),
        ('Configuration', {
            'fields': ('is_recurring', 'is_paid', 'applicable_departments')
        }),
        ('System', {
            'fields': ('is_active', 'created_by'),
            'classes': ('collapse',)
        })
    )
