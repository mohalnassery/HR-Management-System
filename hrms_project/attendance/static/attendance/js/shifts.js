// Function to check for overlapping shifts
async function checkOverlappingShifts() {
    const employeeSelect = document.getElementById('employee');
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');

    if (!employeeSelect || !startDateInput) return;

    const employeeId = employeeSelect.value;
    const startDate = startDateInput.value;
    const endDate = endDateInput?.value || startDate;
    const currentAssignmentId = new URLSearchParams(window.location.search).get('id');

    if (!employeeId || !startDate) return;

    try {
        const response = await fetch(`/api/attendance/check-shift-overlap/?employee=${employeeId}&start_date=${startDate}&end_date=${endDate}${currentAssignmentId ? `&exclude=${currentAssignmentId}` : ''}`);
        const data = await response.json();
        
        const form = document.getElementById('shift-assignment-form');
        if (!form) return;

        let warningElement = document.getElementById('overlap-warning');
        if (data.overlapping) {
            if (!warningElement) {
                const warningDiv = document.createElement('div');
                warningDiv.id = 'overlap-warning';
                warningDiv.className = 'alert alert-warning mt-3';
                warningDiv.innerHTML = `
                    <i class="fas fa-exclamation-triangle"></i>
                    Warning: This assignment overlaps with existing shift assignments:
                    <ul>
                        ${data.overlapping.map(overlap => `
                            <li>${overlap.shift_name}: ${overlap.start_date} to ${overlap.end_date || 'Permanent'}</li>
                        `).join('')}
                    </ul>
                `;
                const lastFormGroup = form.querySelector('.mb-3:last-child');
                if (lastFormGroup) {
                    form.insertBefore(warningDiv, lastFormGroup);
                } else {
                    form.appendChild(warningDiv);
                }
            }
        } else if (warningElement) {
            warningElement.remove();
        }
    } catch (error) {
        console.error('Error checking shift overlap:', error);
    }
}

// Function to update night shift indicator
function updateNightShiftIndicator() {
    const shiftSelect = document.getElementById('shift');
    const nightShiftIndicator = document.getElementById('night-shift-indicator');
    
    if (!shiftSelect || !nightShiftIndicator) return;

    const selectedOption = shiftSelect.options[shiftSelect.selectedIndex];
    if (!selectedOption) return;

    const isNightShift = selectedOption.dataset.shiftType === 'NIGHT';
    nightShiftIndicator.style.display = isNightShift ? 'block' : 'none';
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize calendar if element exists
    const calendarEl = document.getElementById('shift-assignment-calendar');
    if (calendarEl) {
        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            height: '800px',
            events: function(info, successCallback, failureCallback) {
                // Get filter values
                const departmentFilter = document.getElementById('department-filter-calendar')?.value || '';
                const employeeFilter = document.getElementById('employee-filter-calendar')?.value || '';
                const shiftTypeFilter = document.getElementById('shift-type-filter-calendar')?.value || '';

                // Fetch events from API
                fetch(`/attendance/api/shift_assignment_calendar_events/?start=${info.startStr}&end=${info.endStr}&department=${departmentFilter}&employee_id=${employeeFilter}&shift_type=${shiftTypeFilter}`)
                    .then(response => response.json())
                    .then(data => {
                        successCallback(data);
                    })
                    .catch(error => {
                        console.error('Error fetching events:', error);
                        failureCallback(error);
                    });
            },
            eventContent: function(arg) {
                return {
                    html: `
                        <div class="fc-event-title">${arg.event.title}</div>
                        <div class="fc-event-time">${arg.event.extendedProps.shift_timing || ''}</div>
                    `
                };
            },
            dateClick: function(info) {
                // Handle date click if needed
            },
            eventClick: function(info) {
                // Handle event click if needed
            }
        });

        calendar.render();

        // Add filter change handlers if elements exist
        const departmentFilter = document.getElementById('department-filter-calendar');
        const employeeFilter = document.getElementById('employee-filter-calendar');
        const shiftTypeFilter = document.getElementById('shift-type-filter-calendar');
        const viewModeSelect = document.getElementById('view-mode-calendar');

        if (departmentFilter) {
            departmentFilter.addEventListener('change', () => calendar.refetchEvents());
        }
        if (employeeFilter) {
            employeeFilter.addEventListener('change', () => calendar.refetchEvents());
        }
        if (shiftTypeFilter) {
            shiftTypeFilter.addEventListener('change', () => calendar.refetchEvents());
        }
        if (viewModeSelect) {
            viewModeSelect.addEventListener('change', (e) => calendar.changeView(e.target.value));
        }
    }

    // Quick assignment form handlers
    const quickAssignmentForm = document.getElementById('quick-assignment-form');
    if (quickAssignmentForm) {
        const employeeSelect = document.getElementById('employee');
        const shiftSelect = document.getElementById('shift');
        const startDateInput = document.getElementById('start_date');
        const endDateInput = document.getElementById('end_date');

        // Initialize night shift indicator if elements exist
        if (shiftSelect) {
            updateNightShiftIndicator();
            shiftSelect.addEventListener('change', updateNightShiftIndicator);
        }

        // Check for overlaps when form inputs change
        [employeeSelect, startDateInput, endDateInput].forEach(element => {
            if (element) {
                element.addEventListener('change', checkOverlappingShifts);
            }
        });

        // Handle form submission
        quickAssignmentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            fetch('/attendance/api/shift-assignments/quick/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const calendarEl = document.getElementById('shift-assignment-calendar');
                    if (calendarEl) {
                        const calendar = new FullCalendar.Calendar(calendarEl);
                        calendar.refetchEvents();
                    }
                    bootstrap.Modal.getInstance(document.getElementById('quickAssignmentModal')).hide();
                } else {
                    alert(data.error || 'Failed to create assignment');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to create assignment');
            });
        });
    }
});
