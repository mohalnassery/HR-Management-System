// Utility Functions
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatTime(time) {
    if (!time) return '-';
    return time.substring(0, 5); // HH:mm format
}

// Calendar Functions
class AttendanceCalendar {
    constructor(elementId, options = {}) {
        this.calendar = new FullCalendar.Calendar(document.getElementById(elementId), {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,dayGridWeek'
            },
            events: this.fetchEvents.bind(this),
            eventClick: this.handleEventClick.bind(this),
            ...options
        });

        this.calendar.render();
    }

    async fetchEvents(info, successCallback, failureCallback) {
        try {
            const response = await fetch(
                `/api/attendance/calendar-events/?start=${info.startStr}&end=${info.endStr}`
            );
            const data = await response.json();
            
            const events = data.map(event => ({
                title: event.title,
                start: event.date,
                backgroundColor: this.getStatusColor(event.status),
                extendedProps: {
                    attendance_id: event.id,
                    status: event.status,
                    employee: event.employee_name
                }
            }));

            successCallback(events);
        } catch (error) {
            failureCallback(error);
        }
    }

    handleEventClick(info) {
        const { attendance_id } = info.event.extendedProps;
        showAttendanceDetails(attendance_id);
    }

    getStatusColor(status) {
        const colors = {
            'present': '#28a745',
            'absent': '#dc3545',
            'late': '#ffc107',
            'leave': '#17a2b8',
            'holiday': '#007bff'
        };
        return colors[status] || '#6c757d';
    }

    refresh() {
        this.calendar.refetchEvents();
    }
}

// Attendance List Functions
class AttendanceList {
    constructor(options = {}) {
        this.page = 1;
        this.filters = {};
        this.setupEventListeners();
        this.options = options;
    }

    setupEventListeners() {
        // Date range filters
        document.getElementById('start-date')?.addEventListener('change', () => this.loadData());
        document.getElementById('end-date')?.addEventListener('change', () => this.loadData());
        
        // Other filters
        document.getElementById('department-filter')?.addEventListener('change', () => this.loadData());
        document.getElementById('status-filter')?.addEventListener('change', () => this.loadData());
        
        // Search input with debounce
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            let timeout;
            searchInput.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => this.loadData(), 500);
            });
        }

        // File upload handling
        const uploadBtn = document.getElementById('upload-btn');
        if (uploadBtn) {
            uploadBtn.addEventListener('click', () => this.handleFileUpload());
        }
    }

    async loadData(page = 1) {
        this.page = page;
        this.filters = {
            start_date: document.getElementById('start-date')?.value,
            end_date: document.getElementById('end-date')?.value,
            department: document.getElementById('department-filter')?.value,
            status: document.getElementById('status-filter')?.value,
            search: document.getElementById('search-input')?.value
        };

        const params = new URLSearchParams({
            ...this.filters,
            page: this.page
        });

        try {
            const response = await fetch(`/api/attendance/logs/?${params}`);
            const data = await response.json();
            
            this.updateTable(data.results);
            this.updatePagination(data.total_pages, data.current_page);
            this.updateSummary(data.summary);
            
        } catch (error) {
            console.error('Error loading attendance data:', error);
        }
    }

    updateTable(records) {
        const tbody = document.querySelector('#attendance-table tbody');
        if (!tbody) return;

        tbody.innerHTML = records.map(record => `
            <tr>
                <td>${record.employee_number}</td>
                <td>${record.employee_name}</td>
                <td>${record.department}</td>
                <td>${formatDate(record.date)}</td>
                <td>${formatTime(record.first_in_time)}</td>
                <td>${formatTime(record.last_out_time)}</td>
                <td>
                    <span class="badge bg-${this.getStatusBadgeClass(record.status)}">
                        ${record.status}
                    </span>
                </td>
                <td>${record.source}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="editAttendance(${record.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    updatePagination(totalPages, currentPage) {
        const pagination = document.getElementById('pagination');
        if (!pagination) return;

        let html = '';
        if (totalPages > 1) {
            html = this.generatePaginationHTML(currentPage, totalPages);
        }
        pagination.innerHTML = html;
    }

    generatePaginationHTML(currentPage, totalPages) {
        return `
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="attendanceList.loadData(${currentPage - 1})">Previous</a>
            </li>
            ${Array.from({ length: totalPages }, (_, i) => i + 1).map(page => `
                <li class="page-item ${currentPage === page ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="attendanceList.loadData(${page})">${page}</a>
                </li>
            `).join('')}
            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="attendanceList.loadData(${currentPage + 1})">Next</a>
            </li>
        `;
    }

    updateSummary(summary) {
        for (const [key, value] of Object.entries(summary)) {
            const element = document.getElementById(`${key}-count`);
            if (element) {
                element.textContent = value;
            }
        }
    }

    getStatusBadgeClass(status) {
        const classes = {
            'present': 'success',
            'absent': 'danger',
            'late': 'warning',
            'leave': 'info',
            'holiday': 'primary'
        };
        return classes[status] || 'secondary';
    }

    async handleFileUpload() {
        const fileInput = document.getElementById('attendance-file');
        if (!fileInput?.files[0]) {
            alert('Please select a file to upload');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const response = await fetch('/api/attendance/records/upload_excel/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }

            alert(`Successfully processed ${data.records_created} records`);
            this.loadData();
            bootstrap.Modal.getInstance(document.getElementById('uploadModal')).hide();
            
        } catch (error) {
            alert('Error uploading file: ' + error.message);
        } finally {
            fileInput.value = '';
        }
    }
}

// Leave Management Functions
class LeaveManager {
    constructor() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        const submitBtn = document.getElementById('submit-leave');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.submitLeaveRequest());
        }
    }

    async submitLeaveRequest() {
        const form = document.getElementById('leave-form');
        const formData = new FormData(form);

        try {
            const response = await fetch('/api/attendance/leaves/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }

            alert('Leave request submitted successfully');
            window.location.reload();
            
        } catch (error) {
            alert('Error submitting leave request: ' + error.message);
        }
    }

    async updateLeaveStatus(leaveId, status, remarks = '') {
        try {
            const response = await fetch(`/api/attendance/leaves/${leaveId}/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ status, remarks })
            });

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }

            window.location.reload();
            
        } catch (error) {
            alert('Error updating leave status: ' + error.message);
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize components based on current page
    if (document.getElementById('attendance-calendar')) {
        window.calendar = new AttendanceCalendar('attendance-calendar');
    }
    
    if (document.getElementById('attendance-table')) {
        window.attendanceList = new AttendanceList();
        window.attendanceList.loadData();
    }
    
    if (document.getElementById('leave-form')) {
        window.leaveManager = new LeaveManager();
    }
});