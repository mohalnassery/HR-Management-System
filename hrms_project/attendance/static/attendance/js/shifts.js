// Global variables
let selectedEmployeeId = null;
let calendar = null;

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

// Initialize calendar
function initializeCalendar() {
    const calendarEl = document.getElementById('shift-assignment-calendar');
    if (!calendarEl) return;

    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        slotMinTime: '00:00:00',
        slotMaxTime: '24:00:00',
        allDaySlot: false,
        height: '800px',
        slotDuration: '01:00:00',
        dayMaxEvents: true,
        displayEventTime: true,
        nextDayThreshold: '00:00:00',
        eventTimeFormat: {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        },
        views: {
            timeGridDay: {
                type: 'timeGrid',
                duration: { days: 1 }
            },
            timeGridWeek: {
                type: 'timeGrid',
                duration: { weeks: 1 }
            },
            dayGridMonth: {
                type: 'dayGrid',
                duration: { months: 1 }
            }
        },
        events: function(info, successCallback, failureCallback) {
            try {
                // Build query parameters
                const params = new URLSearchParams({
                    start: info.startStr,
                    end: info.endStr,
                    view: info.view?.type || 'dayGridMonth'
                });
                
                const departmentFilter = document.getElementById('departmentFilter');
                const shiftTypeFilter = document.getElementById('shiftTypeFilter');
                
                if (selectedEmployeeId) {
                    params.append('employee_id', selectedEmployeeId);
                }
                if (departmentFilter?.value) {
                    params.append('department_id', departmentFilter.value);
                }
                if (shiftTypeFilter?.value) {
                    params.append('shift_type', shiftTypeFilter.value);
                }
                
                fetch(`/attendance/api/shift_assignment_calendar_events/?${params}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        const formattedEvents = data.map(event => ({
                            ...event,
                            allDay: false,
                            display: 'block',
                            className: [
                                ...(event.className || []),
                                'shift-event',
                                `shift-type-${event.shift_type.toLowerCase()}`
                            ]
                        }));
                        successCallback(formattedEvents);
                    })
                    .catch(error => {
                        console.error('Error fetching events:', error);
                        failureCallback(error);
                    });
            } catch (error) {
                console.error('Error in events function:', error);
                failureCallback(error);
            }
        },
        eventContent: function(arg) {
            try {
                const shiftType = arg.event.extendedProps?.shift_type || 'DEFAULT';
                const className = `shift-type-${shiftType.toLowerCase()}`;
                const timeText = arg.event.extendedProps?.shift_timing || 
                    `${arg.event.start?.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - 
                     ${arg.event.end?.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
                
                // Different display for month view vs week/day view
                if (arg.view.type === 'dayGridMonth') {
                    return {
                        html: `
                            <div class="fc-event-main-wrapper ${className}">
                                <div class="fc-event-title">${arg.event.title || ''}</div>
                                <div class="fc-event-time">${timeText}</div>
                                <div class="fc-event-type">${shiftType}</div>
                            </div>
                        `
                    };
                } else {
                    // For week/day view, show a more compact version
                    return {
                        html: `
                            <div class="fc-event-main-wrapper ${className}">
                                <div class="fc-event-title">${arg.event.title || ''}</div>
                                <div class="fc-event-type">${shiftType}</div>
                            </div>
                        `
                    };
                }
            } catch (error) {
                console.error('Error in eventContent:', error);
                return {
                    html: '<div>Error displaying event</div>'
                };
            }
        },
        dateClick: function(info) {
            try {
                if (selectedEmployeeId) {
                    // If employee selected, show assignment modal
                    const modal = new bootstrap.Modal(document.getElementById('employeeSearchModal'));
                    document.getElementById('selectedDate').value = info.dateStr;
                    modal.show();
                } else {
                    // If no employee selected, show day detail view
                    window.location.href = `/attendance/shifts/day/${info.dateStr}/`;
                }
            } catch (error) {
                console.error('Error in dateClick:', error);
            }
        }
    });

    return calendar;
}

// Initialize employee search functionality
function initializeEmployeeSearch() {
    const searchInput = document.getElementById('employeeSearch');
    const searchResults = document.getElementById('searchResults');
    const selectedEmployeeDiv = document.getElementById('selectedEmployee');
    const clearEmployeeBtn = document.getElementById('clearEmployee');
    
    if (!searchInput || !searchResults || !selectedEmployeeDiv || !clearEmployeeBtn) return;

    let searchTimeout;

    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            searchResults.classList.remove('show');
            return;
        }

        searchTimeout = setTimeout(() => {
            fetch(`/attendance/api/search_employees/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    // Debug log to see the structure of the API response
                    console.log('API Response:', data);
                    if (data.length > 0) {
                        console.log('First employee data:', data[0]);
                    }

                    searchResults.innerHTML = data.map(emp => {
                        // Debug log for each employee object
                        console.log('Processing employee:', emp);
                        const employeeName = emp.full_name || emp.get_full_name || `${emp.first_name} ${emp.last_name}`.trim();
                        console.log('Resolved employee name:', employeeName);
                        
                        return `
                            <div class="employee-item" data-id="${emp.id}" data-name="${employeeName}" data-number="${emp.employee_number}">
                                ${employeeName} (${emp.employee_number})
                            </div>
                        `;
                    }).join('');
                    searchResults.classList.add('show');
                });
        }, 300);
    });

    searchResults.addEventListener('click', function(e) {
        const item = e.target.closest('.employee-item');
        if (item) {
            selectedEmployeeId = item.dataset.id;
            selectedEmployeeDiv.innerHTML = `
                <div class="selected-employee">
                    <span>${item.dataset.name} (${item.dataset.number})</span>
                    <button type="button" class="btn btn-sm btn-outline-danger remove-employee">
                        <i class="bi bi-x"></i>
                    </button>
                </div>
            `;
            searchResults.classList.remove('show');
            searchInput.value = '';
            if (calendar) calendar.refetchEvents();
        }
    });

    clearEmployeeBtn.addEventListener('click', function() {
        selectedEmployeeId = null;
        selectedEmployeeDiv.innerHTML = '';
        if (calendar) calendar.refetchEvents();
    });

    // Close search results when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.remove('show');
        }
    });
}

// Initialize modal employee search
function initializeModalEmployeeSearch() {
    const searchInput = document.getElementById('modalEmployeeSearch');
    const modalEmployeeList = document.getElementById('modalEmployeeList');
    const modalDepartmentFilter = document.getElementById('modalDepartmentFilter');
    const confirmButton = document.getElementById('confirmEmployeeSelection');
    
    if (!searchInput || !modalEmployeeList || !modalDepartmentFilter || !confirmButton) return;

    let searchTimeout;

    // Employee search functionality
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            return;
        }

        searchTimeout = setTimeout(() => {
            // Filter existing employees in the list
            document.querySelectorAll('#modalEmployeeList .employee-item').forEach(item => {
                const label = item.querySelector('.form-check-label');
                const text = label.textContent.toLowerCase();
                const department = modalDepartmentFilter.value;
                const empDepartment = item.dataset.department;
                
                const matchesSearch = text.includes(query.toLowerCase());
                const matchesDepartment = !department || empDepartment === department;
                
                item.style.display = matchesSearch && matchesDepartment ? '' : 'none';
            });
        }, 300);
    });

    // Department filter
    modalDepartmentFilter.addEventListener('change', function() {
        const department = this.value;
        document.querySelectorAll('#modalEmployeeList .employee-item').forEach(item => {
            const empDepartment = item.dataset.department;
            item.style.display = (!department || empDepartment === department) ? '' : 'none';
        });
    });

    // Handle employee selection confirmation
    confirmButton.addEventListener('click', function() {
        const selectedDate = document.getElementById('selectedDate').value;
        const selectedEmployees = [];
        
        document.querySelectorAll('#modalEmployeeList .employee-checkbox:checked').forEach(checkbox => {
            selectedEmployees.push({
                id: checkbox.value,
                fullname: checkbox.dataset.fullname,
                number: checkbox.dataset.number,
                department: checkbox.dataset.department
            });
        });

        if (selectedEmployees.length > 0) {
            // Here you can handle the selected employees and date
            console.log('Selected Date:', selectedDate);
            console.log('Selected Employees:', selectedEmployees);
            
            // Update calendar
            if (calendar) calendar.refetchEvents();
        }

        // Close the modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('employeeSearchModal'));
        if (modal) modal.hide();
    });
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize calendar
    calendar = initializeCalendar();
    if (calendar) {
        // Fix calendar rendering on tab change
        document.querySelector('button[data-bs-target="#calendar-view"]')?.addEventListener('shown.bs.tab', function (e) {
            setTimeout(() => calendar.render(), 0);
        });
        calendar.render();
    }

    // Initialize search functionalities
    initializeEmployeeSearch();
    initializeModalEmployeeSearch();

    // Initialize filters
    const departmentFilter = document.getElementById('departmentFilter');
    const shiftTypeFilter = document.getElementById('shiftTypeFilter');
    
    departmentFilter?.addEventListener('change', () => calendar?.refetchEvents());
    shiftTypeFilter?.addEventListener('change', () => calendar?.refetchEvents());

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

// Add this CSS to the existing styles
const styles = `
    .shift-type-default {
        background-color: #0d6efd !important;
        border-color: #0a58ca !important;
        color: white !important;
    }
    .shift-type-night {
        background-color: #0dcaf0 !important;
        border-color: #0a9ec0 !important;
        color: black !important;
    }
    .shift-type-open {
        background-color: #6c757d !important;
        border-color: #565e64 !important;
        color: white !important;
    }
    .shift-event {
        margin: 1px 0;
        padding: 2px;
        border-radius: 3px;
    }
    .fc-event-main-wrapper {
        padding: 2px 4px;
    }
    .fc-event-title {
        font-weight: bold;
        margin-bottom: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .fc-event-time {
        font-size: 0.9em;
        opacity: 0.9;
    }
    .fc-event-type {
        font-size: 0.8em;
        opacity: 0.8;
        font-style: italic;
    }
    .fc-timegrid-event {
        min-height: 2em !important;
    }
    .fc-timegrid-event .fc-event-main {
        padding: 2px 4px !important;
    }
    .fc-timegrid-event .fc-event-title {
        font-size: 0.9em;
    }
    .fc-timegrid-event .fc-event-type {
        font-size: 0.8em;
    }
`;

// Add the styles to the document
const styleSheet = document.createElement('style');
styleSheet.textContent = styles;
document.head.appendChild(styleSheet);
