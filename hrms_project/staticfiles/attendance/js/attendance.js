// Initialize calendar and event handlers
document.addEventListener('DOMContentLoaded', function() {
    initializeCalendar();
    initializeLeaveForm();
    initializeAttendanceMarking();
    setupDateRangePicker();
});

// Calendar Functions
function initializeCalendar() {
    const calendarEl = document.getElementById('attendance-calendar');
    if (!calendarEl) return;

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: '/attendance/api/calendar-events/',
        eventDidMount: function(info) {
            // Add tooltips to events
            const status = info.event.extendedProps.status;
            const timeIn = info.event.extendedProps.first_in || '';
            const timeOut = info.event.extendedProps.last_out || '';
            
            tippy(info.el, {
                content: `
                    <strong>Status:</strong> ${status}<br>
                    <strong>Time In:</strong> ${timeIn}<br>
                    <strong>Time Out:</strong> ${timeOut}
                `,
                allowHTML: true
            });
        },
        eventClick: function(info) {
            showAttendanceDetail(info.event);
        }
    });

    calendar.render();
}

function showAttendanceDetail(event) {
    // Fetch and display attendance details in modal
    fetch(`/attendance/api/logs/${event.id}/details/`)
        .then(response => response.json())
        .then(data => {
            const modal = new bootstrap.Modal(document.getElementById('attendance-detail-modal'));
            document.getElementById('attendance-detail-content').innerHTML = `
                <div class="attendance-detail">
                    <h5>Attendance Details</h5>
                    <div class="detail-row">
                        <strong>Date:</strong> ${data.date}
                    </div>
                    <div class="detail-row">
                        <strong>Status:</strong> ${data.status}
                    </div>
                    <div class="detail-row">
                        <strong>Time In:</strong> ${data.first_in || '-'}
                    </div>
                    <div class="detail-row">
                        <strong>Time Out:</strong> ${data.last_out || '-'}
                    </div>
                    <div class="detail-row">
                        <strong>Source:</strong> ${data.source}
                    </div>
                </div>
            `;
            modal.show();
        })
        .catch(error => console.error('Error:', error));
}

// Leave Request Functions
function initializeLeaveForm() {
    const leaveForm = document.getElementById('leave-request-form');
    if (!leaveForm) return;

    const leaveTypeSelect = document.getElementById('leave_type');
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');

    // Update leave balance display when type changes
    leaveTypeSelect?.addEventListener('change', function() {
        updateLeaveBalance(this.value);
    });

    // Calculate duration when dates change
    [startDateInput, endDateInput].forEach(input => {
        input?.addEventListener('change', function() {
            if (startDateInput.value && endDateInput.value) {
                calculateLeaveDuration(startDateInput.value, endDateInput.value);
            }
        });
    });

    // Handle form submission
    leaveForm.addEventListener('submit', function(e) {
        e.preventDefault();
        submitLeaveRequest(new FormData(this));
    });
}

function updateLeaveBalance(leaveTypeId) {
    if (!leaveTypeId) return;

    fetch(`/attendance/api/leave-balance/${leaveTypeId}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('leave-balance-display').innerHTML = `
                Available: ${data.available_days} days<br>
                Consumed: ${data.consumed_days} days
            `;
        })
        .catch(error => console.error('Error:', error));
}

function calculateLeaveDuration(startDate, endDate) {
    fetch('/attendance/api/calculate-leave-duration/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ start_date: startDate, end_date: endDate })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('duration-display').textContent = 
            `Duration: ${data.duration} days`;
    })
    .catch(error => console.error('Error:', error));
}

function submitLeaveRequest(formData) {
    fetch('/attendance/api/leave-requests/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Leave request submitted successfully');
            setTimeout(() => window.location.href = '/attendance/leaves/', 2000);
        } else {
            showAlert('danger', data.error || 'Error submitting leave request');
        }
    })
    .catch(error => {
        showAlert('danger', 'Error submitting leave request');
        console.error('Error:', error);
    });
}

// Attendance Marking Functions
function initializeAttendanceMarking() {
    const markAttendanceForm = document.getElementById('mark-attendance-form');
    if (!markAttendanceForm) return;

    markAttendanceForm.addEventListener('submit', function(e) {
        e.preventDefault();
        submitAttendance(new FormData(this));
    });

    // Initialize employee search typeahead
    const employeeInput = document.getElementById('employee_search');
    if (employeeInput) {
        new Bloodhound({
            datumTokenizer: Bloodhound.tokenizers.obj.whitespace('value'),
            queryTokenizer: Bloodhound.tokenizers.whitespace,
            remote: {
                url: '/attendance/api/search-employees/?q=%QUERY',
                wildcard: '%QUERY'
            }
        });

        $(employeeInput).typeahead(null, {
            name: 'employees',
            display: 'full_name',
            source: employeeEngine
        });
    }
}

function submitAttendance(formData) {
    fetch('/attendance/api/mark-attendance/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Attendance marked successfully');
            document.getElementById('mark-attendance-form').reset();
        } else {
            showAlert('danger', data.error || 'Error marking attendance');
        }
    })
    .catch(error => {
        showAlert('danger', 'Error marking attendance');
        console.error('Error:', error);
    });
}

// Utility Functions
function setupDateRangePicker() {
    const dateRangePicker = document.getElementById('date-range');
    if (!dateRangePicker) return;

    $(dateRangePicker).daterangepicker({
        autoUpdateInput: false,
        locale: {
            cancelLabel: 'Clear'
        }
    });

    $(dateRangePicker).on('apply.daterangepicker', function(ev, picker) {
        $(this).val(picker.startDate.format('MM/DD/YYYY') + ' - ' + picker.endDate.format('MM/DD/YYYY'));
        updateDateRange(picker.startDate, picker.endDate);
    });

    $(dateRangePicker).on('cancel.daterangepicker', function(ev, picker) {
        $(this).val('');
    });
}

function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const alertContainer = document.getElementById('alert-container');
    if (alertContainer) {
        alertContainer.appendChild(alertDiv);
        setTimeout(() => alertDiv.remove(), 5000);
    }
}

function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// Handle Back Button
window.addEventListener('popstate', function(e) {
    if (e.state && e.state.modal) {
        // Close any open modals when using browser back button
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) modalInstance.hide();
        });
    }
});
