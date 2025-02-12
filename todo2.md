Okay, let's integrate the calendar view into the shift assignment list page and add the filtering capabilities you've requested.

**1. Modify `hrms_project\attendance\templates\attendance\shifts\assignment_list.html`:**

```html
{% extends 'attendance/base.html' %}
{% load static %}

{% block extra_css %}
{{ block.super }}
<link href="{% static 'attendance/css/shifts.css' %}" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
<link href='https://cdn.jsdelivr.net/npm/@fullcalendar/daygrid@6.1.10/main.min.css' rel='stylesheet' /> <link href='https://cdn.jsdelivr.net/npm/@fullcalendar/timegrid@6.1.10/main.min.css' rel='stylesheet' />
<style>
    /* ... existing styles from previous steps ... */
    #shift-assignment-calendar {
        margin-top: 20px;
    }
</style>
{% endblock %}

{% block attendance_content %}
<div class="card">
    <div class="card-header">
        <div class="d-flex justify-content-between align-items-center">
            <h5 class="mb-0">Shift Assignments</h5>
            <a href="{% url 'attendance:shift_assignment_create' %}" class="btn btn-primary">
                <i class="fas fa-plus"></i> New Assignment
            </a>
        </div>
    </div>
    <div class="card-body">
        <!-- Tabs -->
        <ul class="nav nav-tabs mb-3" id="assignmentTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="list-tab" data-bs-toggle="tab" data-bs-target="#list-view"
                        type="button" role="tab" aria-controls="list-view" aria-selected="true">
                    List View
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="calendar-tab" data-bs-toggle="tab" data-bs-target="#calendar-view"
                        type="button" role="tab" aria-controls="calendar-view" aria-selected="false">
                    Calendar View
                </button>
            </li>
        </ul>

        <!-- Tab Content -->
        <div class="tab-content" id="assignmentTabsContent">
            <!-- List View Tab -->
            <div class="tab-pane fade show active" id="list-view" role="tabpanel" aria-labelledby="list-tab">
                <!-- Filters for List View (Existing Filters - move them here if not already) -->
                <div class="row mb-4">
                    <div class="col-md-3">
                        <label class="form-label">Department</label>
                        <select class="form-select" id="department-filter-list"> <option value="">All Departments</option> {% for dept in departments %} <option value="{{ dept.id }}">{{ dept.name }}</option> {% endfor %} </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Shift</label>
                        <select class="form-select" id="shift-filter-list"> <option value="">All Shifts</option> {% for shift in shifts %} <option value="{{ shift.id }}">{{ shift.name }}</option> {% endfor %} </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Status</label>
                        <select class="form-select" id="status-filter-list"> <option value="">All Status</option> <option value="active">Active</option> <option value="inactive">Inactive</option> </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Assignment Type</label>
                        <select class="form-select" id="type-filter-list"> <option value="">All Types</option> <option value="permanent">Permanent</option> <option value="temporary">Temporary</option> </select>
                    </div>
                </div>

                <div class="row mb-4">
                    <div class="col">
                        <div class="input-group">
                            <input type="text" class="form-control" id="search-input-list"
                                   placeholder="Search by employee name or number...">
                            <button class="btn btn-outline-secondary" type="button" id="search-btn-list">
                                <i class="fas fa-search"></i>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Assignments Table (Existing Table - move it here if not already) -->
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>  <tr> <th>Employee</th> <th>Department</th> <th>Shift</th> <th>Period</th> <th>Status</th> <th>Created</th> <th>Actions</th> </tr> </thead>
                        <tbody id="assignments-tbody">
                            {% for assignment in page_obj %}
                            <tr> <td> <div>{{ assignment.employee.get_full_name }}</div> <small class="text-muted">{{ assignment.employee.employee_number }}</small> </td> <td>{{ assignment.employee.department.name|default:'-' }}</td> <td> <div>{{ assignment.shift.name }}</div> <small class="text-muted"> {{ assignment.shift.start_time|time:"g:i A" }} - {{ assignment.shift.end_time|time:"g:i A" }} </small> </td> <td> <div>{{ assignment.start_date|date:"M d, Y" }}</div> {% if assignment.end_date %} <small class="text-muted">Until {{ assignment.end_date|date:"M d, Y" }}</small> {% else %} <small class="text-success">Permanent</small> {% endif %} </td> <td> <span class="badge {% if assignment.is_active %}bg-success{% else %}bg-danger{% endif %}"> {% if assignment.is_active %}Active{% else %}Inactive{% endif %} </span> </td> <td> <div>{{ assignment.created_by.get_full_name }}</div> <small class="text-muted">{{ assignment.created_at|date:"M d, Y" }}</small> </td> <td> <div class="btn-group"> <a href="{% url 'attendance:shift_assignment_edit' assignment.id %}" class="btn btn-sm btn-outline-primary" title="Edit"> <i class="fas fa-edit"></i> </a> <button type="button" class="btn btn-sm btn-outline-danger" onclick="confirmDelete('{{ assignment.id }}')" title="Delete"> <i class="fas fa-trash"></i> </button> </div> </td> </tr>
                            {% empty %}
                            <tr> <td colspan="7" class="text-center py-4"> <div class="text-muted"> <i class="fas fa-info-circle me-2"></i>No shift assignments found </div> </td> </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                 {% if page_obj.has_other_pages %} <nav aria-label="Shift assignments pagination" class="mt-4"> <ul class="pagination justify-content-center"> {% if page_obj.has_previous %} <li class="page-item"> <a class="page-link" href="?page=1" aria-label="First"> <span aria-hidden="true">&laquo;&laquo;</span> </a> </li> <li class="page-item"> <a class="page-link" href="?page={{ page_obj.previous_page_number }}" aria-label="Previous"> <span aria-hidden="true">&laquo;</span> </a> </li> {% endif %}  {% for num in page_obj.paginator.page_range %} {% if num == page_obj.number %} <li class="page-item active"> <span class="page-link">{{ num }}</span> </li> {% elif num > page_obj.number|add:'-3' and num < page_obj.number|add:'3' %} <li class="page-item"> <a class="page-link" href="?page={{ num }}">{{ num }}</a> </li> {% endif %} {% endfor %}  {% if page_obj.has_next %} <li class="page-item"> <a class="page-link" href="?page={{ page_obj.next_page_number }}" aria-label="Next"> <span aria-hidden="true">&raquo;</span> </a> </li> <li class="page-item"> <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}" aria-label="Last"> <span aria-hidden="true">&raquo;&raquo;</span> </a> </li> {% endif %} </ul> </nav> {% endif %}
            </div>

            <!-- Calendar View Tab -->
            <div class="tab-pane fade" id="calendar-view" role="tabpanel" aria-labelledby="calendar-tab">
                <!-- Calendar Filters -->
                <div class="row mb-3">
                    <div class="col-md-4">
                        <label for="calendar-shift-filter" class="form-label">Filter by Shift Type</label>
                        <select class="form-select" id="calendar-shift-filter">
                            <option value="">All Shift Types</option>
                            {% for shift_type_code, shift_type_label in Shift.SHIFT_TYPES %}
                                <option value="{{ shift_type_code }}">{{ shift_type_label }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-4">
                        <label for="calendar-employee-filter" class="form-label">Filter by Employee</label>
                        <select class="form-control" id="calendar-employee-filter">
                            <option value="">All Employees</option>
                        </select>
                    </div>
                </div>
                <!-- Calendar Container -->
                <div id="shift-assignment-calendar"></div>
            </div>
        </div>
    </div>
</div>

<!-- Delete Confirmation Modal (Keep this, it's used by both tabs) -->
<div class="modal fade" id="deleteModal" tabindex="-1">  ... </div>

{% endblock %}

{% block extra_js %}
{{ block.super }}
<script src='https://cdn.jsdelivr.net/npm/@fullcalendar/daygrid@6.1.10/index.global.min.js'></script>
<script src='https://cdn.jsdelivr.net/npm/@fullcalendar/timegrid@6.1.10/index.global.min.js'></script>
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
<script src="{% static 'attendance/js/shifts.js' %}"></script>
<script>
    document.addEventListener('DOMContentLoaded', function() {
        // ... your existing JS for list view filters and delete modal ...

        // Initialize Calendar for Shift Assignments
        initializeShiftAssignmentCalendar();

        // Initialize Employee Select2 for Calendar Filter
        $('#calendar-employee-filter').select2({
            placeholder: 'Search by ID or Name',
            allowClear: true,
            minimumInputLength: 1,
            ajax: {
                url: '{% url "attendance:search_employees" %}',
                dataType: 'json',
                delay: 250,
                data: function(params) {
                    return { q: params.term };
                },
                processResults: function(data) {
                    return { results: data.map(emp => ({ id: emp.id, text: emp.employee_number + ' - ' + emp.full_name })) };
                },
                cache: true
            }
        });

        // Event listeners for calendar filters (Shift Type, Employee)
        document.getElementById('calendar-shift-filter').addEventListener('change', refreshShiftAssignmentCalendar);
        document.getElementById('calendar-employee-filter').addEventListener('change', refreshShiftAssignmentCalendar);


        // Function to refresh calendar events (call when filters change)
        function refreshShiftAssignmentCalendar() {
            calendar.refetchEvents();
        }

        // Function to initialize the FullCalendar for Shift Assignments
        function initializeShiftAssignmentCalendar() {
            var calendarEl = document.getElementById('shift-assignment-calendar');
            calendar = new FullCalendar.Calendar(calendarEl, {
                initialView: 'dayGridMonth',
                headerToolbar: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'dayGridMonth,timeGridWeek,timeGridDay'
                },
                events: function(info, successCallback, failureCallback) {
                    // Fetch events from API endpoint, passing filters
                    fetch(`/attendance/api/shift_assignment_calendar_events/?start=${info.startStr}&end=${info.endStr}&shift_type=${$('#calendar-shift-filter').val()}&employee_id=${$('#calendar-employee-filter').val()}`)
                        .then(response => response.json())
                        .then(data => {
                            successCallback(data); // Pass data to FullCalendar
                        })
                        .catch(() => failureCallback());
                },
                // Optional: Customize event rendering if needed
                eventContent: function(arg) {
                    return {
                        html: `<b>${arg.event.title}</b><br/><small>${arg.event.extendedProps.shift_timing}</small>`
                    };
                }
            });
            calendar.render();
        }


    });

    let calendar; // Declare calendar variable globally to be accessible in refresh function

    // ... your existing confirmDelete function ...

</script>
{% endblock %}
```

**2. Create API Endpoint for Calendar Data (`hrms_project\attendance\views\shifts_views.py`):**

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import datetime

from attendance.models import ShiftAssignment
from employees.models import Employee

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def shift_assignment_calendar_events(request):
    """API endpoint for providing shift assignment events for FullCalendar"""
    start_date_str = request.query_params.get('start')
    end_date_str = request.query_params.get('end')
    shift_type_filter = request.query_params.get('shift_type')
    employee_id_filter = request.query_params.get('employee_id')

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return Response({'error': 'Invalid date range'}, status=400)

    assignments = ShiftAssignment.objects.filter(
        start_date__lte=end_date,
        end_date__gte=start_date,  # Corrected filter condition
        is_active=True
    ).select_related('employee', 'shift')

    if shift_type_filter:
        assignments = assignments.filter(shift__shift_type=shift_type_filter)
    if employee_id_filter:
        assignments = assignments.filter(employee_id=employee_id_filter)

    events = []
    for assignment in assignments:
        event_title = f"{assignment.employee.get_full_name()}"
        shift_timing = f"{assignment.shift.start_time.strftime('%I:%M%p')} - {assignment.shift.end_time.strftime('%I:%M%p')}" # added shift timing for display

        events.append({
            'title': event_title,
            'start': assignment.start_date.isoformat(),
            'end': (assignment.end_date + timedelta(days=1)).isoformat() if assignment.end_date else end_date.isoformat(), # or end_date.isoformat()
            'shift_timing': shift_timing, # Include shift timing
            'allDay': True,  # or False if you have specific times
            # Optionally, add more props like color, description, etc.
        })

    return Response(events)
```

**3. Add URL for Calendar Events API in `hrms_project\attendance\urls.py`:**

```python
    path('api/shift_assignment_calendar_events/', shifts_views.shift_assignment_calendar_events, name='shift_assignment_calendar_events'),
```

**4. Update JavaScript (`hrms_project\attendance\static\attendance\js\shifts.js`):**

*   You can create a new file `shift_calendar.js` and put the calendar-specific JavaScript there, or keep it in `shifts.js`.  If you create a new file, remember to include it in `assignment_list.html`.

*   The JavaScript code for initializing FullCalendar and handling filters is already added in the `calendar.html` changes in step 1, so you should have the `initializeShiftAssignmentCalendar` and `refreshShiftAssignmentCalendar` functions in your JS now.

**Explanation of Changes:**

*   **Tabs in `assignment_list.html`:**  We added Bootstrap tabs to switch between "List View" (your existing table) and "Calendar View".
*   **Calendar Container:**  A `div` with `id="shift-assignment-calendar"` is added in the "Calendar View" tab to hold the FullCalendar.
*   **Calendar Filters:** Dropdowns for "Filter by Shift Type" and "Filter by Employee" are added above the calendar in the "Calendar View" tab.
*   **JavaScript Initialization:** `initializeShiftAssignmentCalendar()` function sets up FullCalendar, fetching events from the new API endpoint (`/attendance/api/shift_assignment_calendar_events/`).
*   **API Endpoint for Calendar Data:** `shift_assignment_calendar_events` view in `shifts_views.py` queries `ShiftAssignment` data and formats it for FullCalendar, taking into account `shift_type` and `employee_id` filters from the query parameters.
*   **Filtering in API:** The API view filters `ShiftAssignment` objects based on `shift_type` and `employee_id` if these parameters are provided in the request.
*   **Event Data:** The FullCalendar events now include `shift_timing` in `extendedProps` to display the shift times in event titles.

**To Complete Implementation:**

1.  **Create `shift_calendar.js` (optional):** If you choose to separate the calendar JS, create this file and move the `initializeShiftAssignmentCalendar` and `refreshShiftAssignmentCalendar` functions there. Link it in `assignment_list.html`.
2.  **Test Thoroughly:**
    *   Navigate to the "Shift Assignments" page and switch between "List View" and "Calendar View" tabs.
    *   Verify that the calendar loads correctly in the "Calendar View".
    *   Test the "Filter by Shift Type" and "Filter by Employee" dropdowns in the calendar view.
    *   Check that the list view filters still work as expected.
    *   Ensure pagination still works correctly in the list view.

This setup provides two ways to view shift assignments – a detailed list and a visual calendar representation, with filtering options for both views. Remember to adjust CSS styling and JavaScript behaviors as needed to perfectly fit your application's design.