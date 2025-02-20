import {
    getReportParameters,
    handleExportFormat,
    formatDate,
    showLoadingState,
    hideLoadingState,
    showError
} from './report_utils.js';

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
        showError('Error checking shift overlap');
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
        events: async function(info, successCallback, failureCallback) {
            try {
                showLoadingState();
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
                
                const response = await fetch(`/attendance/api/shift_assignment_calendar_events/?${params}`);
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                
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
            } catch (error) {
                console.error('Error fetching events:', error);
                failureCallback(error);
                showError('Error fetching calendar events');
            } finally {
                hideLoadingState();
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
                showError('Error handling date click');
            }
        }
    });

    return calendar;
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
        quickAssignmentForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            try {
                showLoadingState();
                const formData = new FormData(this);
                
                const response = await fetch('/attendance/api/shift-assignments/quick/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                });
                
                const data = await response.json();
                if (data.success) {
                    calendar?.refetchEvents();
                    bootstrap.Modal.getInstance(document.getElementById('quickAssignmentModal')).hide();
                } else {
                    throw new Error(data.error || 'Failed to create assignment');
                }
            } catch (error) {
                console.error('Error:', error);
                showError(error.message || 'Failed to create assignment');
            } finally {
                hideLoadingState();
            }
        });
    }
});

// Add the styles
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
