---

### **Implementation Commands**

1. **Define Shift Types:**
   - **Supported Shift Types:**  
     - **Default Shift (7AM–4PM):**  
       - Automatically applied if no specific shift is selected for an employee.
       - Represents 8 hours of work plus a 1‑hour auto-deducted break (9 hours total).
     - **Night Shift:**  
       - Must be manually selected.
       - Represents 8 hours of work plus a 1‑hour break (9 hours total).
       - **Multi-Day Handling:**  
         - Support shifts that span midnight (e.g., starting at 10 PM on one day and finishing at 7 AM the next).  
         - Implement logic to detect if the clock‑out time is earlier than the clock‑in time and adjust by adding one day.
     - **Open Shift:**  
       - Employee‑defined start time, selected manually.
       - Also represents 8 hours of work plus a 1‑hour auto‑deducted break (9 hours total).
   - **Defaulting Rule:**  
     - If no shift type is selected for an employee, the system automatically assigns the Default Shift.

2. **Data Model Updates:**
   - **ShiftAssignment Model:**  
     - Include fields such as:
       - `employee`: Foreign key to the Employee model.
       - `shift_type`: A character field with choices for Default, Night, and Open (default set to Default).
       - `start_date` and (optional) `end_date` for temporary assignments (a null end date indicates a permanent assignment).
       - *(Optionally)* A field (for example, `shift_end_datetime`) to accurately capture the end time for Night shifts spanning midnight.
     - Ensure all shift assignments are recorded in the database for historical reporting.
   - **RamadanDates Table:**  
     - Create a dedicated table (e.g., `RamadanDates`) with fields such as:
       - `year` (or a date range identifier).
       - `start_date` and `end_date` for Ramadan in that year.
     - **Purpose:**  
       - Manually specify Ramadan periods for each year.  
       - Allow the system to reference historical Ramadan dates for consistent shift calculations.

3. **Calculation Logic:**
   - **Normal Calculation (Non‑Ramadan):**  
     - For any shift (Default, Night, or Open) where the employee is either not Muslim or the date is outside any defined Ramadan period, calculate total hours as:  
       **(Clock Out – Clock In) – 1 hour** (to account for the auto‑deducted break), resulting in 8 hours of work.
   - **Ramadan Calculation:**  
     - If an employee’s HRMS record indicates `religion = "Muslim"` and the shift date falls within any of the manually defined Ramadan periods (from the RamadanDates table), then calculate total hours as:  
       **Clock Out – Clock In** (with no break deduction).
   - **Night Shift Multi‑Day Handling:**  
     - For Night shifts, detect if the clock‑out time is earlier than the clock‑in time.  
     - If so, add one day to the clock‑out time before performing the above calculations.

4. **System Configuration:**
   - **Admin Panel Enhancements:**  
     - Provide controls to configure settings such as:
       - The grace period duration (if applicable) and other break duration rules.
       - Multi‑day shift handling options.
     - **Ramadan Dates Management:**  
       - Include an interface to add, update, and view Ramadan periods in the dedicated RamadanDates table.
       - Ensure historical Ramadan periods are preserved for consistency in reporting.

5. **UI Enhancements:**
   - **Shift Assignment Interface:**  
     - Develop a calendar view interface for managing shift assignments.
     - Provide a dropdown selector that lists the three shift types: Default, Night, and Open.
     - Display clear visual warnings for overlapping shifts and indicate when a shift spans midnight.
     - Allow for date‑range override assignments.
   - **Historical Data:**  
     - Ensure that all shift assignments are stored with their corresponding dates so that historical data (past years’ shifts) can be reviewed.
     
6. **Base Template Update (base.html):**
   - **UI Command:**  
     - Update the `base.html` template to add a new sidebar button labeled “Shift Management.”
     - Ensure the new button is styled consistently with existing sidebar items (e.g., Daily Attendance, Holiday Management, Leave Management, Calendar Views).
     - Link the button to the Shift Management interface.

---

### **Summary of Behavior:**

- **Normal Days:**  
  - Every shift (Default, Night, Open) is treated uniformly with an auto‑deduction of 1 hour (regardless of the number of punches) so that the employee effectively works 8 hours.

- **Ramadan (for Muslim employees):**  
  - The auto‑deducted break is not applied; total hours are calculated directly as the difference between clock‑in and clock‑out times.
  - Non‑Muslim employees continue to follow the normal calculation.

- **Historical Tracking:**  
  - All shift assignments, including past years, are maintained in the database.
  - Ramadan dates are manually entered and preserved in a dedicated table for consistency.
