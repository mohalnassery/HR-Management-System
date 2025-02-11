Okay, let's address your requests step-by-step to enhance the shift management, especially for night shifts, and improve shift assignments.

**1. Fix Shift Type Dropdown in Forms:**

**Modify `hrms_project\attendance\views\shifts_views.py`:**

In both `shift_create` and `shift_edit` views, we need to pass the `SHIFT_TYPES` choices to the template context.

```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import transaction
from django.urls import reverse
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..serializers import ShiftSerializer

from attendance.models import Shift, ShiftAssignment
from employees.models import Employee


class ShiftViewSet(viewsets.ModelViewSet):
    """ViewSet for managing shifts through the API"""
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [IsAuthenticated]


@login_required
def shift_list(request):
    """View for listing all shifts"""
    shifts = Shift.objects.all().order_by('start_time')
    return render(request, 'attendance/shifts/shift_list.html', {'shifts': shifts})

@login_required
def shift_create(request):
    """View for creating a new shift"""
    if request.method == 'POST':
        # ... (rest of your POST handling code remains the same)
        pass

    context = {
        'shift_types': Shift.SHIFT_TYPES # Pass SHIFT_TYPES to context
    }
    return render(request, 'attendance/shifts/shift_form.html', context) # Pass context here

@login_required
def shift_edit(request, pk):
    """View for editing an existing shift"""
    shift = get_object_or_404(Shift, pk=pk)

    if request.method == 'POST':
        # ... (rest of your POST handling code remains the same)
        pass

    context = {
        'shift': shift,
        'shift_types': Shift.SHIFT_TYPES # Pass SHIFT_TYPES to context
    }
    return render(request, 'attendance/shifts/shift_form.html', context) # Pass context here

# ... (rest of your shifts_views.py code)
```

**Modify `hrms_project\attendance\templates\attendance\shifts\shift_form.html`:**

Update the `<select>` element for `shift_type` to iterate through `shift_types` from the context.

```html
<div class="mb-3">
    <label class="form-label">Shift Type*</label>
    <select class="form-select" name="shift_type" required="">
        <option value="">Select Shift Type</option>
        {% for type_code, type_label in shift_types %}  {# Iterate through shift_types #}
            <option value="{{ type_code }}" {% if shift.shift_type == type_code %}selected{% endif %}>
                {{ type_label }}
            </option>
        {% endfor %}
    </select>
</div>
```

Now, when you access the shift creation or edit form, you should see the "Default Shift," "Night Shift," and "Open Shift" options in the "Shift Type" dropdown.

**2. Flexible Night Shift Timing (Calendar and Form-based):**

To implement flexible night shift timing, we'll start with a simpler form-based approach and later consider a calendar integration if needed.

**Model Change (Optional - for day-specific overrides, if needed later):**

For now, let's assume you want a more general approach to handle night shifts. We can use the existing `is_night_shift` field in the `Shift` model and potentially add a default night shift time range.  If you need day-specific timings in the future, we can add a new model like `NightShiftOverride`.

**Enhancements to `hrms_project\attendance\models.py` (optional):**

If you want a default night shift time:

```python
# hrms_project\attendance\models.py

class Shift(models.Model):
    # ... (existing fields)
    default_night_start_time = models.TimeField(null=True, blank=True, help_text="Default start time for night shift")
    default_night_end_time = models.TimeField(null=True, blank=True, help_text="Default end time for night shift")
    # ... (rest of the model)
```

**Update `hrms_project\attendance\templates\attendance\shifts\shift_form.html`:**

Add fields for default night shift start and end times:

```html
{# hrms_project\attendance\templates\attendance\shifts\shift_form.html #}

{# ... (existing form fields) #}

                <!-- Additional Settings -->
                <div class="col-md-6">
                    {# ... (existing grace_period and break_duration fields) #}

                    <div class="mb-3" id="nightShiftTimingFields" style="display: none;">
                        <label class="form-label">Default Night Shift Start Time</label>
                        <input type="time" class="form-control" name="default_night_start_time"
                               value="{{ shift.default_night_start_time|time:'H:i'|default:'' }}">
                    </div>

                    <div class="mb-3" id="nightShiftTimingFields_end" style="display: none;">
                        <label class="form-label">Default Night Shift End Time</label>
                        <input type="time" class="form-control" name="default_night_end_time"
                               value="{{ shift.default_night_end_time|time:'H:i'|default:'' }}">
                    </div>
                </div>

                {# ... (is_night_shift and is_active checkboxes and submit buttons) #}
```

**Update JavaScript in `hrms_project\attendance\templates\attendance\shifts\shift_form.html`:**

To show/hide the night shift timing fields based on the `is_night_shift` checkbox:

```javascript
{# hrms_project\attendance\templates\attendance\shifts\shift_form.html #}

{# ... (existing javascript) #}

    isNightShiftCheckbox.addEventListener('change', function() {
        const nightShiftTimingFields = document.getElementById('nightShiftTimingFields');
        const nightShiftTimingFields_end = document.getElementById('nightShiftTimingFields_end');
        if (this.checked) {
            nightShiftTimingFields.style.display = 'block';
            nightShiftTimingFields_end.style.display = 'block';
        } else {
            nightShiftTimingFields.style.display = 'none';
            nightShiftTimingFields_end.style.display = 'none';
        }
    });

    // Check initial state on page load
    if (isNightShiftCheckbox.checked) {
        document.getElementById('nightShiftTimingFields').style.display = 'block';
        document.getElementById('nightShiftTimingFields_end').style.display = 'block';
    }

{# ... (rest of javascript) #}
```

**Modify `hrms_project\attendance\views\shifts_views.py` to handle new fields:**

```python
# hrms_project\attendance\views\shifts_views.py

@login_required
def shift_create(request):
    """View for creating a new shift"""
    if request.method == 'POST':
        # ... (existing fields)
        default_night_start_time = request.POST.get('default_night_start_time')
        default_night_end_time = request.POST.get('default_night_end_time')

        shift = Shift.objects.create(
            # ... (existing fields)
            default_night_start_time=default_night_start_time,
            default_night_end_time=default_night_end_time,
        )
        # ... (rest of create view)

    context = {
        'shift_types': Shift.SHIFT_TYPES
    }
    return render(request, 'attendance/shifts/shift_form.html', context)

@login_required
def shift_edit(request, pk):
    """View for editing an existing shift"""
    shift = get_object_or_404(Shift, pk=pk)

    if request.method == 'POST':
        # ... (existing fields)
        shift.default_night_start_time = request.POST.get('default_night_start_time')
        shift.default_night_end_time = request.POST.get('default_night_end_time')
        # ... (rest of edit view)

    context = {
        'shift': shift,
        'shift_types': Shift.SHIFT_TYPES
    }
    return render(request, 'attendance/shifts/shift_form.html', context)
```

Now you can set default start and end times for Night Shifts in the Shift form. If you set `is_night_shift` to `True`, these new time fields will be displayed.

**3. Employee Multi-Select for Shift Assignment:**

**Modify `hrms_project\attendance\templates\attendance\shifts\assignment_form.html`:**

Change the employee selection to a multi-select using `<select multiple>` and update the label:

```html
{# hrms_project\attendance\templates\attendance\shifts\assignment_form.html #}

<div class="mb-3">
    <label class="form-label">Employees</label> <small class="text-muted">(Select multiple employees)</small>
    <select class="form-select" id="employee" name="employee" multiple required>  {# Add multiple attribute #}
        {% for employee in employees %}
            <option value="{{ employee.id }}" {% if employee.id in form.employee.value|list %}selected{% endif %}> {# Adjust selection logic for multiple values #}
                {{ employee.get_full_name }} ({{ employee.employee_number }})
            </option>
        {% endfor %}
    </select>
</div>
```

**Modify `hrms_project\attendance\views\shifts_views.py` to handle multi-select and bulk assignment:**

Update `shift_assignment_create` and `shift_assignment_edit` views to process the list of employee IDs.

```python
# hrms_project\attendance\views\shifts_views.py

@login_required
def shift_assignment_create(request):
    """View for creating a new shift assignment"""
    if request.method == 'POST':
        employee_ids = request.POST.getlist('employee') # Use getlist to get multiple values
        shift_id = request.POST.get('shift')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date') or None
        is_active = request.POST.get('is_active') == 'on'

        try:
            with transaction.atomic():
                created_count = 0
                for employee_id in employee_ids: # Iterate through employee IDs
                    # Deactivate any existing active assignments for each employee
                    ShiftAssignment.objects.filter(
                        employee_id=employee_id,
                        is_active=True
                    ).update(is_active=False)

                    # Create new assignment
                    ShiftAssignment.objects.create(
                        employee_id=employee_id,
                        shift_id=shift_id,
                        start_date=start_date,
                        end_date=end_date,
                        is_active=is_active,
                        created_by=request.user
                    )
                    created_count += 1

                messages.success(request, f'{created_count} Shift assignments created successfully.') # Update success message
                return redirect('attendance:shift_assignment_list')

        except Exception as e:
            messages.error(request, f'Error assigning shift: {str(e)}')

    employees = Employee.objects.filter(is_active=True)
    shifts = Shift.objects.filter(is_active=True)

    return render(request, 'attendance/shifts/assignment_form.html', {
        'employees': employees,
        'shifts': shifts
    })

@login_required
def shift_assignment_edit(request, pk):
    """View for editing a shift assignment"""
    assignment = get_object_or_404(ShiftAssignment, pk=pk)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # If making this assignment active, deactivate other active assignments (this part might be less relevant in edit as you are editing a specific assignment)
                # if request.POST.get('is_active') == 'on' and not assignment.is_active:
                #     ShiftAssignment.objects.filter(
                #         employee=assignment.employee,
                #         is_active=True
                #     ).exclude(pk=pk).update(is_active=False)

                assignment.shift_id = request.POST.get('shift')
                assignment.start_date = request.POST.get('start_date')
                assignment.end_date = request.POST.get('end_date') or None
                assignment.is_active = request.POST.get('is_active') == 'on'
                assignment.save()

                messages.success(request, 'Shift assignment updated successfully.')
                return redirect('attendance:shift_assignment_list')

        except Exception as e:
            messages.error(request, f'Error updating shift assignment: {str(e)}')

    employees = Employee.objects.filter(is_active=True)
    shifts = Shift.objects.filter(is_active=True)

    return render(request, 'attendance/shifts/assignment_form.html', {
        'form': assignment,
        'employees': employees,
        'shifts': shifts
    })
```

With these changes, you should now have:

*   A populated "Shift Type" dropdown in the shift form.
*   Basic form fields for setting default night shift timings (you can enhance this further).
*   Multi-select functionality in the shift assignment form to assign shifts to multiple employees at once.

Remember to apply migrations after model changes if you added `default_night_start_time` and `default_night_end_time` fields.

Next steps would be:

*   **Calendar-based Night Shift Scheduling:** Implement the calendar view for day-specific night shift timing overrides.
*   **Verification of Shift Type Behavior:** Review and test the code to ensure the shift type behaviors (break deduction, Ramadan handling) are as described in your summary.
*   **Unit Tests:** Write unit tests to cover the new night shift timing features and the bulk shift assignment functionality.