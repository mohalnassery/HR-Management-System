from datetime import datetime, timedelta
from typing import Optional

from django.utils import timezone

from ..models import Shift
from .ramadan_service import RamadanService

class AttendanceStatusService:
    @staticmethod
    def calculate_status(attendance_log):
        """
        Calculate attendance status based on attendance log, considering:
        - Shift type-specific timings
        - Ramadan adjustments for Muslim employees
        - Night shift overrides
        - Grace periods
        """
        # Check existing status for leave and holiday
        if attendance_log.status in ['leave', 'holiday']:
            return attendance_log.status
        elif not attendance_log.first_in_time:
            return 'absent'

        shift = attendance_log.shift
        if not shift:
            # Try to get default shift if none assigned
            shift = Shift.objects.filter(
                shift_type='DEFAULT',
                is_active=True
            ).first()
            if not shift:
                return 'absent'  # No shift assigned and no default shift available
            attendance_log.shift = shift  # Update log with default shift

        # Get shift timings using ShiftService
        from .shift_service import ShiftService
        shift_timing = ShiftService.get_shift_timing(shift, attendance_log.date)
        shift_start_time = shift_timing['start_time']
        shift_end_time = shift_timing['end_time']

        # Check for night shift override
        if shift.shift_type == 'NIGHT':
            from attendance.models import DateSpecificShiftOverride
            override = DateSpecificShiftOverride.objects.filter(
                date=attendance_log.date,
                shift_type='NIGHT'
            ).first()
            if override:
                if override.override_start_time:
                    shift_start_time = override.override_start_time
                if override.override_end_time:
                    shift_end_time = override.override_end_time

        # Calculate lateness
        grace_minutes = shift.grace_period or 0
        shift_start_with_grace = (
            datetime.combine(attendance_log.date, shift_start_time) + 
            timedelta(minutes=grace_minutes)
        ).time()

        # Handle night shift that crosses midnight
        is_late = False
        late_minutes = 0
        if shift.shift_type == 'NIGHT' and shift_end_time < shift_start_time:
            # For night shifts, if check-in is after midnight, compare with previous day
            if attendance_log.first_in_time < shift_start_time:
                # Employee checked in after midnight but before shift end
                is_late = attendance_log.first_in_time > shift_start_with_grace
            else:
                # Employee checked in before midnight
                is_late = attendance_log.first_in_time > shift_start_with_grace
        else:
            # Regular shift timing comparison
            is_late = attendance_log.first_in_time > shift_start_with_grace

        if is_late:
            late_minutes = int(
                (datetime.combine(attendance_log.date, attendance_log.first_in_time) -
                datetime.combine(attendance_log.date, shift_start_time))
                .total_seconds() / 60
            )

        # Update attendance log with lateness info
        attendance_log.is_late = is_late
        attendance_log.late_minutes = late_minutes
        attendance_log.save(update_fields=['is_late', 'late_minutes'])

        return 'late' if is_late else 'present'
    
    @staticmethod
    def calculate_work_duration(attendance_log, employee) -> int:
        """
        Calculate work duration in minutes taking into account:
        - Regular shifts: Deduct 1-hour break
        - Ramadan period for Muslim employees: No break deduction
        - Night shifts: Handle midnight spanning

        Args:
            attendance_log: The AttendanceLog instance
            employee: The Employee instance

        Returns:
            int: Total work duration in minutes
        """
        if not attendance_log.first_in_time or not attendance_log.last_out_time:
            return 0

        # Convert times to datetime for calculations
        date = attendance_log.date
        first_in = datetime.combine(date, attendance_log.first_in_time)
        last_out = datetime.combine(date, attendance_log.last_out_time)

        shift = attendance_log.shift
        if not shift:
            return 0

        # First check for Ramadan timings if employee is Muslim
        if attendance_log.employee.religion == "Muslim":
            ramadan_timing = RamadanService.get_ramadan_shift_timing(shift, attendance_log.date)
            if ramadan_timing:
                shift_start_time = ramadan_timing['start_time']
                shift_end_time = ramadan_timing['end_time']
            else:
                # Get regular shift timings if not in Ramadan period
                from .shift_service import ShiftService
                shift_timing = ShiftService.get_shift_timing(shift, attendance_log.date)
                shift_start_time = shift_timing['start_time']
                shift_end_time = shift_timing['end_time']
        else:
            # Non-Muslim employees use regular shift timings
            from .shift_service import ShiftService
            shift_timing = ShiftService.get_shift_timing(shift, attendance_log.date)
            shift_start_time = shift_timing['start_time']
            shift_end_time = shift_timing['end_time']

        # Handle night shift spanning midnight
        if shift.shift_type == 'NIGHT' and shift_end_time < shift_start_time:
            if last_out.time() < first_in.time():
                # Add one day to last_out for correct duration calculation
                last_out += timedelta(days=1)

        # Calculate base duration
        duration = int((last_out - first_in).total_seconds() / 60)  # Convert to minutes

        # Check if employee is Muslim and date falls in Ramadan
        ramadan_period = RamadanService.get_active_period(attendance_log.date)
        is_muslim_employee = employee.religion == "Muslim"

        if ramadan_period and is_muslim_employee:
            if shift.ramadan_end_time:
                # Use Ramadan-specific end time to calculate duration
                expected_hours = (
                    datetime.combine(date, shift.ramadan_end_time) - 
                    datetime.combine(date, shift_start_time)
                ).seconds / 3600
            else:
                # Calculate Ramadan hours if no specific end time is set
                normal_hours = (
                    datetime.combine(date, shift_end_time) - 
                    datetime.combine(date, shift_start_time)
                ).seconds / 3600
                expected_hours = RamadanService.calculate_working_hours(normal_hours, is_ramadan=True)

            # Convert expected hours to minutes for comparison
            expected_minutes = int(expected_hours * 60)
            duration = min(duration, expected_minutes)
        else:
            # For non-Ramadan or non-Muslim employees, deduct break duration
            duration -= shift.break_duration

        return max(duration, 0)  # Ensure non-negative duration

    @staticmethod
    def update_attendance_status(attendance_log):
        """
        Update the attendance log with status, lateness, and work duration
        """
        # Calculate status (updates is_late and late_minutes)
        status = AttendanceStatusService.calculate_status(attendance_log)
        
        # Calculate work duration
        work_duration = AttendanceStatusService.calculate_work_duration(
            attendance_log,
            attendance_log.employee
        )
        
        # Update log
        attendance_log.status = status
        attendance_log.total_work_minutes = work_duration
        attendance_log.save(
            update_fields=['status', 'total_work_minutes']
        )
        
        return status
