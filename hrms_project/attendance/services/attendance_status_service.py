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