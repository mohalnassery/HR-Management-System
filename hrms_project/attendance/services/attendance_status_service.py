from datetime import datetime, timedelta
from typing import Optional

from django.utils import timezone

from .ramadan_service import RamadanService

class AttendanceStatusService:
    @staticmethod
    def calculate_status(attendance_log):
        """
        Calculate attendance status based on attendance log
        """
        if attendance_log.is_leave:
            return 'leave'
        elif attendance_log.is_holiday:
            return 'holiday'
        elif not attendance_log.first_in_time:
            return 'absent'
        elif attendance_log.is_late:
            return 'late'
        return 'present'
    
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

        # Handle night shift spanning midnight
        if attendance_log.shift and attendance_log.shift.is_night_shift:
            if last_out.time() < first_in.time():
                # Add one day to last_out for correct duration calculation
                last_out += timedelta(days=1)

        # Calculate base duration
        duration = int((last_out - first_in).total_seconds() / 60)  # Convert to minutes

        # Check if employee is Muslim and date falls in Ramadan
        is_ramadan_exempt = (
            employee.religion == "Muslim" and 
            RamadanService.get_active_period(attendance_log.date) is not None
        )

        # For non-Ramadan or non-Muslim employees, deduct break duration
        if not is_ramadan_exempt and attendance_log.shift:
            duration -= attendance_log.shift.break_duration

        return max(duration, 0)  # Ensure non-negative duration
