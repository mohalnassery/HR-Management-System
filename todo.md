**Objective of the To-Do List:**

The primary objective of this to-do list is to **enhance the shift management functionality of the HRMS attendance system to be more flexible, accurate, and aligned with real-world shift scheduling needs.**  This includes:

*   **Supporting diverse shift types:**  Implementing distinct shift types (Default, Open, Night) beyond a single "regular" shift, each with potentially different default timings and rules.
*   **Accurate Lateness Calculation:** Ensuring the system correctly identifies and logs lateness based on the defined shift type, timings, and grace periods, taking into account factors like night shifts and Ramadan.
*   **Flexibility for Night Shifts:** Providing a mechanism to handle date-specific timing adjustments for night shifts, recognizing that night shift schedules can vary.
*   **Ramadan Compliance:** Automatically adjusting shift durations and rules for Muslim employees during Ramadan, respecting religious observances.
*   **Improved User Experience:** Enhancing the administrative interface for managing shifts and overrides, making it more intuitive and efficient.

**Current Implementation (As-Is):**

Currently, the shift implementation is **partially complete and somewhat basic**.  Here's a summary of what exists:

*   **Shift and Shift Assignment Models:** The database models for `Shift` and `ShiftAssignment` are in place, allowing for the definition of shifts with basic attributes (name, start/end time, break, grace) and assignment of these shifts to employees for specific periods.
*   **Admin Interface for Shift Management:**  Admin interfaces (`ShiftAdmin`, `ShiftAssignmentAdmin`) exist for managing shifts and their assignments through the Django admin panel.
*   **Basic Attendance Logging:**  The `AttendanceLog` model can record attendance status and times, and the admin interface can display this information, including a status that can be "late."
*   **Initial Lateness Detection Framework (Partially Implemented):** There are signals and a service (`AttendanceStatusService`) designed to *calculate* attendance status and lateness, but the automatic triggering and complete logic for lateness calculation and logging are likely **not fully active or comprehensive.**
*   **Missing Key Features:**  The system currently **lacks**:
    *   Explicit handling of different shift *types* (Default, Open, Night) with distinct default timings.
    *   Automated and accurate lateness detection based on shift type, grace periods, and specific times.
    *   Proper handling of cross-day night shifts in calculations.
    *   Built-in Ramadan-specific shift adjustments.
    *   User-friendly calendar-based configuration for date-specific shift overrides.

**Desired Achievement (To-Be):**

After completing the to-do list, the HRMS attendance system will achieve the following:

*   **Robust Shift Type Management:**  Administrators will be able to define and manage "Default," "Open," and "Night" shift types, each with configurable default timings and rules.
*   **Automated and Accurate Lateness Logging:** The system will automatically and accurately determine and log employee lateness based on their assigned shift type, specified timings, and grace periods.  This will be reflected in the `AttendanceLog` and visible in reports and the admin interface.
*   **Intelligent Night Shift Handling:** The system will correctly process attendance for night shifts that span across midnight, ensuring accurate duration and status calculations.
*   **Ramadan-Aware Attendance:** For Muslim employees during Ramadan, the system will automatically adjust shift durations and calculations to reflect reduced working hours.
*   **Flexible Night Shift Scheduling:** Administrators will have a calendar-based interface to define and manage date-specific timing overrides for night shifts, allowing for exceptions to the default night shift schedule.
*   **Improved Administrative Workflow:** The admin interface for shift management will be more user-friendly and efficient for configuring and managing diverse shift schedules.
*   **Comprehensive Testing and Validation:** The system will be thoroughly tested to ensure the accuracy and reliability of the enhanced shift management and lateness logging features.

In essence, the to-do list aims to transform the current, somewhat basic shift handling into a **feature-rich, flexible, and accurate shift management system** that meets the specific needs outlined, including handling complex scenarios like night shifts and Ramadan, and providing clear logging of attendance status, including lateness.




**To-Do List: Implement Enhanced Shift Workflow**

**Phase 1: Database Model Changes (Foundation)**

1.  **Modify `Shift` Model (`hrms_project/attendance/models.py`):**
    *   **(a) Update `SHIFT_TYPES`:**
        ```python
        SHIFT_TYPES = [
            ('DEFAULT', 'Default Shift'),
            ('OPEN', 'Open Shift'),
            ('NIGHT', 'Night Shift'),
        ]
        ```
    *   **(b) Remove `is_night_shift` Field:** Delete the line `is_night_shift = models.BooleanField(default=False)` from the `Shift` model.
    *   **(c) Add `default_start_time` and `default_end_time` Fields:** Add these new fields to the `Shift` model:
        ```python
        default_start_time = models.TimeField(
            null=True, blank=True, help_text="Default start time for this shift type"
        )
        default_end_time = models.TimeField(
            null=True, blank=True, help_text="Default end time for this shift type"
        )
        ```
    *   **(d) Create `DateSpecificShiftOverride` Model (`hrms_project/attendance/models.py`):** Add this new model definition:
        ```python
        class DateSpecificShiftOverride(models.Model):
            date = models.DateField(unique=True, help_text="Date for which shift is overridden")
            shift_type = models.CharField(max_length=20, choices=Shift.SHIFT_TYPES, default='NIGHT', help_text="Shift type to override") # Add shift_type
            override_start_time = models.TimeField(null=True, blank=True, help_text="Override start time") # Make nullable and blank for flexibility
            override_end_time = models.TimeField(null=True, blank=True, help_text="Override end time") # Make nullable and blank

            def __str__(self):
                return f"{self.get_shift_type_display()} Override for {self.date}"
        ```

2.  **Create and Apply Migrations:**
    *   **(a) Generate Migrations:** Run the Django command to create migrations:
        ```bash
        python manage.py makemigrations attendance
        ```
    *   **(b) Apply Migrations:** Apply the migrations to your database:
        ```bash
        python manage.py migrate attendance
        ```

**Phase 2: Data Initialization (Seed Data)**

3.  **Modify `init_shift_types` Command (`hrms_project/attendance/management/commands/init_shift_types.py`):**
    *   **(a) Update `DEFAULT_SHIFTS`:** Modify the `DEFAULT_SHIFTS` list in the `Command` class to include `default_start_time` and `default_end_time` for each shift type, and adjust the `shift_type`:
        ```python
        DEFAULT_SHIFTS = [
            {
                'name': 'Default Shift',
                'shift_type': 'DEFAULT',
                'default_start_time': time(7, 0),
                'default_end_time': time(16, 0),
                'break_duration': 60,
                'grace_period': 15,
                'description': 'Standard 7 AM - 4 PM shift'
            },
            {
                'name': 'Open Shift',
                'shift_type': 'OPEN',
                'default_start_time': time(8, 0),
                'default_end_time': time(17, 0),
                'break_duration': 60,
                'grace_period': 30,
                'description': 'Open shift, flexible start, 9 hours total'
            },
            {
                'name': 'Night Shift Default',
                'shift_type': 'NIGHT',
                'default_start_time': time(19, 0),
                'default_end_time': time(4, 0),
                'break_duration': 60,
                'grace_period': 20,
                'description': 'Default Night Shift 7 PM - 4 AM'
            },
        ]
        ```
    *   **(b) Run the Command:** Execute the command to update your Shift data in the database (use `--force` if you want to re-run even if shifts exist):
        ```bash
        python manage.py init_shift_types --force
        ```

**Phase 3: Backend Logic - `AttendanceStatusService` (Core Logic)**

4.  **Modify `AttendanceStatusService.calculate_status` (`hrms_project/attendance/services/attendance_status_service.py`):**
    *   **(a) Ramadan Check:** Add the Ramadan period check and adjust `shift_end_time` for Muslim employees during Ramadan:
        ```python
        # ... inside calculate_status method ...
        shift = attendance_log.shift

        shift_start_time = shift.default_start_time  # Use default start time
        shift_end_time = shift.default_end_time    # Use default end time

        is_ramadan_period = RamadanService.get_active_period(attendance_log.date) is not None
        is_muslim_employee = attendance_log.employee.religion == "Muslim"

        if is_ramadan_period and is_muslim_employee:
            shift_end_time = (datetime.combine(attendance_log.date, shift_start_time) + timedelta(hours=6)).time()
        ```
    *   **(b) Night Shift Override Check:**  Implement the logic to check for `DateSpecificShiftOverride` and use override timings if found for 'NIGHT' shifts:
        ```python
        # ... right after Ramadan check in calculate_status ...
        if shift.shift_type == 'NIGHT':
            override = DateSpecificShiftOverride.objects.filter(
                date=attendance_log.date, shift_type='NIGHT').first() # Filter by shift_type too
            if override:
                if override.override_start_time and override.override_end_time: # Null checks
                    shift_start_time = override.override_start_time
                    shift_end_time = override.override_end_time
        ```
    *   **(c) Lateness and Status Calculation:** Ensure the rest of the `calculate_status` method uses `shift_start_time`, `shift_end_time`, and `shift.grace_period` for lateness, early departure, and status determination.  *(Review your existing `calculate_status` logic to confirm this part is correctly implemented based on the updated shift times)*.

**Phase 4: Signals (Verify and Activate)**

5.  **Activate `process_attendance_record` Signal (`hrms_project/attendance/apps.py`):**
    *   **(a) Uncomment:** In `hrms_project/attendance/apps.py`, uncomment the line that connects the `process_attendance_record` signal in the `AttendanceConfig.ready` method:
        ```python
        post_save.connect(signals.process_attendance_record, sender='attendance.AttendanceRecord')
        ```

6.  **Review `calculate_attendance_status` Signal (`hrms_project/attendance/signals.py`):**
    *   **(a) Verify Logic:** Review the `calculate_attendance_status` signal handler in `hrms_project/attendance/signals.py`. Ensure it is calling `AttendanceStatusService.update_attendance_status(instance)` as expected, or that it contains similar logic to calculate and update the status within the signal handler itself. *If you are using `AttendanceStatusService`, the signal should primarily call the service.*

**Phase 5: Admin Interface Enhancements (User Experience)**

7.  **Update `ShiftAdmin` (`hrms_project/attendance/admin.py`):**
    *   **(a) Display Default Timings:** In `ShiftAdmin.list_display`, add `default_start_time` and `default_end_time` to the `list_display` to make these fields visible in the Shift list view in the admin.
    *   **(b) Form Fields:** Ensure the `ShiftAdmin` form in `admin.py` includes `default_start_time` and `default_end_time` fields for editing.

8.  **Create `DateSpecificShiftOverrideAdmin` (`hrms_project/attendance/admin.py`):**
    *   **(a) Register Admin:** Create a new `ModelAdmin` class for `DateSpecificShiftOverride` and register it in `admin.py`:
        ```python
        @admin.register(DateSpecificShiftOverride)
        class DateSpecificShiftOverrideAdmin(admin.ModelAdmin):
            list_display = ('date', 'shift_type', 'override_start_time', 'override_end_time')
            list_filter = ('shift_type',)
            date_hierarchy = 'date'
            search_fields = ('date',)
        ```
