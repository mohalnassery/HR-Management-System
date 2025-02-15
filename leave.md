
### Comprehensive Plan: Integrating Leave Beginning Balance Management Page into `/attendance/leave_balance/` (Detailed)

**Goal:**

To create a robust and user-friendly system for managing annual leave balances, including:

1.  **Importing Initial Leave Balances (Web-Based):** Implement a web-based interface on the `/attendance/leave_balance/` page for administrators to upload a CSV file containing employee-specific beginning annual leave balances as of a designated cut-off date (e.g., December 31, 2024).
2.  **Displaying Beginning Balances:** Display a clear, sortable list of all imported beginning leave balances directly on the `/attendance/leave_balance/` page for easy review and verification by administrators.
3.  **Automated Annual Leave Accrual (Background Task):** Implement a background task (using Celery) that automatically runs monthly to:
    *   Calculate annual leave accrual for each active employee based on their worked days in the *previous* month (2.5 days accrued for every 30 working days).
    *   Incorporate the imported beginning leave balances into the calculation to ensure accurate starting points for accrual.
    *   Update the `LeaveBalance` records with the calculated accruals and reflect the updated available balances.
4.  **Leave Request Validation (Real-time):** Modify the leave request validation process to:
    *   When an employee applies for annual leave or half-day leave, the system must check against the accurate `available_days` in the `LeaveBalance` model. This balance should reflect both the initial imported balance and any subsequent accruals.
    *   Prevent leave requests from being submitted if the requested duration exceeds the available balance.
5.  **Enhanced User Interface (`/attendance/leave_balance/` Page):**
    *   Improve the `/attendance/leave_balance/` page to serve as a central hub for leave balance management, including:
        *   Displaying the existing employee leave balance summary cards (for quick overview).
        *   Adding a collapsible section containing a user-friendly CSV upload form for importing beginning balances, with clear instructions and error handling.
        *   Integrating a sortable and searchable table to list all imported beginning leave balances, allowing administrators to easily review and verify the imported data.

**Scope:**

*   **Database Model Modification (`hrms_project/attendance/models.py`):**
    *   **Create `LeaveBeginningBalance` Model:** Design and implement a new Django model named `LeaveBeginningBalance` to specifically store the initial annual leave balances. This model will act as a historical record of starting balances as of a particular date.
    *   **Potentially Adjust `LeaveBalance` Model:** Review the existing `LeaveBalance` model to ensure it is optimally structured to work with initial balances and automated accruals. No major structural changes are expected, but verification is needed.

*   **Data Import Functionality (Web-Based - `/attendance/leave_balance/`):**
    *   **CSV Upload Form in Template (`leave_balance.html`):** Design and embed a CSV upload form directly within the `leave_balance.html` template. This form will include:
        *   A file input field for users to upload the CSV file.
        *   A date input field to specify the "as of" date for the balances.
        *   A hidden field for the leave type code (defaulting to 'ANNUAL').
    *   **View Logic in `leave_balance` View (`leave_views.py`):** Implement the CSV import logic within the `leave_balance` view function to:
        *   Handle the file upload from the form.
        *   Validate the CSV file (check for required columns: `employee_number`, `leave_balance`).
        *   Parse the CSV data, read each row, and create `LeaveBeginningBalance` model instances for each employee.
        *   Implement error handling for invalid file formats, missing columns, incorrect data types, and database errors.
        *   Display success and error messages to the user using Django's messages framework.

*   **Accrual Logic (`hrms_project/attendance/tasks.py`):**
    *   **Modify `process_monthly_leave_accruals` Task:** Enhance the Celery task to:
        *   Retrieve the most recent `LeaveBeginningBalance` record for each employee (if one exists) to use as the starting point for calculating the current period's `LeaveBalance`.
        *   Calculate the monthly annual leave accrual based on the employee's worked days in the *previous* month (as currently implemented).
        *   When creating a new `LeaveBalance` record for the current period, initialize `total_days` and `available_days` by summing the retrieved beginning balance (if any) and the calculated monthly accrual.
        *   Ensure that if no beginning balance record exists for an employee, the accrual process starts with a zero initial balance (or a default value if needed).

*   **Leave Request Validation (`hrms_project/attendance/services/leave_request_service.py` - or within the `Leave` model's `clean` method):**
    *   **Update Balance Check:** Modify the leave request validation logic (likely in `LeaveRequestService.validate_leave_request` or the `Leave` model's `clean` method) to:
        *   Fetch the employee's `LeaveBalance` record for the relevant leave type.
        *   Check if the requested leave duration is less than or equal to the `available_days` of the `LeaveBalance`, which now accurately reflects both initial balances and accruals.
        *   Return validation errors if the balance is insufficient.

*   **User Interface Enhancement (`/attendance/leave_balance/`):**
    *   **Enhance `leave_balance.html` Template:** Modify the template to:
        *   Add a clear section for "Import Leave Beginning Balances," including the CSV upload form and instructions.
        *   Integrate a sortable and searchable HTML table to display the `LeaveBeginningBalance` records, showing employee details, leave type, balance, and "as of" date.
        *   Ensure the existing leave balance summary cards remain prominently displayed at the top of the page.
        *   Use Bootstrap CSS classes for styling and responsive design.

**Detailed Steps (Expanded):**

**Step 1: Create the `LeaveBeginningBalance` Model (Detailed)**

*   **File:** `hrms_project/attendance/models.py`
*   **Context:** Define the `LeaveBeginningBalance` model to store initial balances.

```python
# hrms_project/attendance/models.py
from django.db import models
from employees.models import Employee

class LeaveBeginningBalance(models.Model):
    """Stores initial leave balances for employees as of a specific date."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='beginning_balances', verbose_name="Employee") # Links to Employee model, if employee is deleted, balance record also deleted. 'beginning_balances' allows reverse lookup from Employee.
    leave_type = models.ForeignKey('LeaveType', on_delete=models.CASCADE, verbose_name="Leave Type") # ForeignKey to LeaveType, ensures type exists and is linked.
    # Link to LeaveType, specifically 'ANNUAL'. enforeced in code or UI, not DB constraint.
    balance_days = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Balance Days", help_text="Initial leave balance in days.") # DecimalField for accurate representation of leave days, max_digits and decimal_places set the limits.
    as_of_date = models.DateField(help_text="Date when this balance was recorded", verbose_name="As of Date") # DateField to record the cut-off date for the balance.
    created_at = models.DateTimeField(auto_now_add=True) # Automatically set on creation, for audit trail.
    updated_at = models.DateTimeField(auto_now=True)     # Automatically updated on each save, for audit trail.

    class Meta:
        unique_together = ['employee', 'leave_type', 'as_of_date'] # Ensures only one beginning balance record per employee, leave type, and as_of_date combination. Prevents data duplication.
        verbose_name = "Leave Beginning Balance" # Human-readable name for admin interface.
        verbose_name_plural = "Leave Beginning Balances" # Plural form for admin interface.

    def __str__(self):
        return f"{self.employee} - {self.leave_type} - Balance as of {self.as_of_date}" # User-friendly representation in admin and other parts of the application.
```

**Step 2: Create a Migration**

*   **Action:** Run the Django migration command in your terminal.

```bash
python manage.py makemigrations attendance
```

    *   **Explanation:** This command tells Django to examine your models (`models.py`) and create a new migration file in the `hrms_project/attendance/migrations/` directory. The migration file (e.g., `00XX_create_leavebeginningbalance.py`) will contain Python code to create the `LeaveBeginningBalance` table in your database, based on the model definition.
    *   **Verification:** After running `makemigrations`, carefully review the generated migration file to ensure it accurately reflects the model structure you defined in `models.py`. Check for correct field types, constraints, and indexes.

```bash
python manage.py migrate attendance
```

    *   **Explanation:** This command applies the migrations to your database. Django reads the migration files (including the one you just created) and executes the Python code within them to alter your database schema, creating the `attendance_leavebeginningbalance` table and any other necessary database changes.
    *   **Verification:** After running `migrate`, use a database administration tool (like Django's admin interface, or a database client like psql for PostgreSQL, or SQLite browser) to verify that the `attendance_leavebeginningbalance` table has been created in your database with the correct columns and data types as defined in your `LeaveBeginningBalance` model.

**Step 3: Create `LeaveBalanceUploadForm` Form**

*   **File:** `hrms_project/attendance/forms.py`
*   **Context:** Define the Django form to handle CSV file uploads on the web page.

```python
# hrms_project/attendance/forms.py
from django import forms
from .models import Holiday

class HolidayForm(forms.ModelForm):
    # ... HolidayForm code ...
    pass # Keep existing HolidayForm if you have it, or remove if you don't need it

class LeaveBalanceUploadForm(forms.Form): # Create LeaveBalanceUploadForm
    csv_file = forms.FileField( # Field to handle file uploads
        label="CSV File", # User-friendly label for the form field
        help_text="Upload a CSV file with employee_number and leave_balance columns." # Help text to guide users on the expected file format
    )
    as_of_date = forms.DateField( # Field to capture the 'as of' date
        label="Balance as of Date", # User-friendly label
        widget=forms.DateInput(attrs={'type': 'date'}), # Use DateInput widget for a date picker, and set input type to 'date' for HTML5 date input
        help_text="Date to associate with these beginning balances." # Help text for the date field
    )
    leave_type_code = forms.CharField( # Hidden field to pass leave type code
        label="Leave Type Code", # Label (though hidden, good practice to have one)
        initial='ANNUAL', # Set initial value to 'ANNUAL', assuming you're importing annual leave balances
        widget=forms.HiddenInput(), # Use HiddenInput widget to hide this field from the user
    )

    def __init__(self, *args, **kwargs): # Constructor to customize form fields
        super().__init__(*args, **kwargs)
        self.fields['csv_file'].widget.attrs.update({'class': 'form-control'}) # Add Bootstrap 'form-control' class for styling file input
        self.fields['as_of_date'].widget.attrs.update({'class': 'form-control'}) # Add Bootstrap 'form-control' class for styling date input
```

**Step 4: Modify `leave_balance.html` Template**

*   **File:** `hrms_project/attendance/templates/attendance/leave_balance.html`
*   **Context:** Integrate the beginning balance list and CSV import form into the template. (See previously provided code for `leave_balance.html`) - *No changes needed to the code provided before, just ensure you implement it in your template.*

**Step 5: Modify `leave_views.py` View Function**

*   **File:** `hrms_project/attendance/views/leave_views.py`
*   **Context:** Enhance the `leave_balance` view function to handle CSV import and display lists. (See previously provided code for `leave_views.py`) - *No changes needed to the code provided before, just ensure you implement it in your view.*

**Step 6: Modify `process_monthly_leave_accruals` Task**

*   **File:** `hrms_project/attendance/tasks.py`
*   **Context:**  Adjust the task to calculate accrual and incorporate beginning balances. (See previously provided code for `tasks.py`) - *No changes needed to the code provided before, just ensure you implement it in your task.*

**Step 7: Apply Migrations**

```bash
python manage.py makemigrations attendance
python manage.py migrate attendance
```
