document.addEventListener('DOMContentLoaded', function() {
    // Initialize datepickers
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    const departmentSelect = document.getElementById('department');
    const statusSelect = document.getElementById('status');
    const searchInput = document.getElementById('search');
    const reportTable = document.getElementById('report-table');
    const paginationContainer = document.getElementById('pagination');

    // Initialize Select2 for department dropdown if it exists
    if (departmentSelect) {
        $(departmentSelect).select2({
            placeholder: 'Select Department',
            allowClear: true
        });
    }

    // Function to format date for API
    function formatDate(date) {
        if (!date) return '';
        return date;
    }

    // Function to load attendance logs
    function loadAttendanceLogs(page = 1) {
        const params = new URLSearchParams({
            start_date: formatDate(startDateInput.value),
            end_date: formatDate(endDateInput.value),
            department: departmentSelect ? departmentSelect.value : '',
            status: statusSelect ? statusSelect.value : '',
            search: searchInput ? searchInput.value : '',
            page: page
        });

        fetch(`/attendance/api/logs/?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                updateTable(data.results);
                updatePagination(data);
            })
            .catch(error => {
                console.error('Error loading attendance logs:', error);
                showError('Failed to load attendance logs');
            });
    }

    // Function to update table with attendance data
    function updateTable(logs) {
        const tbody = reportTable.querySelector('tbody');
        tbody.innerHTML = '';

        logs.forEach(log => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${log.employee_number}</td>
                <td>${log.employee_name}</td>
                <td>${log.department}</td>
                <td>${log.date}</td>
                <td>${log.first_in || '-'}</td>
                <td>${log.last_out || '-'}</td>
                <td>
                    <span class="badge ${getStatusBadgeClass(log.status)}">
                        ${log.status}
                    </span>
                </td>
                <td>${log.work_duration || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-info view-details" data-id="${log.id}">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });

        // Add click handlers for view details buttons
        document.querySelectorAll('.view-details').forEach(button => {
            button.addEventListener('click', () => viewDetails(button.dataset.id));
        });
    }

    // Function to update pagination
    function updatePagination(data) {
        if (!paginationContainer) return;

        const totalPages = Math.ceil(data.count / 10); // Assuming 10 items per page
        let html = '';

        if (totalPages > 1) {
            html += `
                <nav>
                    <ul class="pagination justify-content-center">
                        <li class="page-item ${data.previous ? '' : 'disabled'}">
                            <a class="page-link" href="#" data-page="${data.current_page - 1}">Previous</a>
                        </li>
            `;

            for (let i = 1; i <= totalPages; i++) {
                html += `
                    <li class="page-item ${i === data.current_page ? 'active' : ''}">
                        <a class="page-link" href="#" data-page="${i}">${i}</a>
                    </li>
                `;
            }

            html += `
                        <li class="page-item ${data.next ? '' : 'disabled'}">
                            <a class="page-link" href="#" data-page="${data.current_page + 1}">Next</a>
                        </li>
                    </ul>
                </nav>
            `;
        }

        paginationContainer.innerHTML = html;

        // Add click handlers for pagination
        paginationContainer.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                if (!link.parentElement.classList.contains('disabled')) {
                    loadAttendanceLogs(parseInt(link.dataset.page));
                }
            });
        });
    }

    // Function to get badge class based on status
    function getStatusBadgeClass(status) {
        const statusClasses = {
            'Present': 'bg-success',
            'Absent': 'bg-danger',
            'Late': 'bg-warning',
            'Leave': 'bg-info',
            'Holiday': 'bg-primary'
        };
        return statusClasses[status] || 'bg-secondary';
    }

    // Function to view attendance details
    function viewDetails(logId) {
        fetch(`/attendance/api/logs/${logId}/`)
            .then(response => response.json())
            .then(data => {
                const modal = new bootstrap.Modal(document.getElementById('detailsModal'));
                document.getElementById('detailsModalContent').innerHTML = `
                    <div class="table-responsive">
                        <table class="table">
                            <tr>
                                <th>Employee</th>
                                <td>${data.employee_name} (${data.employee_number})</td>
                            </tr>
                            <tr>
                                <th>Department</th>
                                <td>${data.department}</td>
                            </tr>
                            <tr>
                                <th>Date</th>
                                <td>${data.date}</td>
                            </tr>
                            <tr>
                                <th>Status</th>
                                <td>
                                    <span class="badge ${getStatusBadgeClass(data.status)}">
                                        ${data.status}
                                    </span>
                                </td>
                            </tr>
                            <tr>
                                <th>First In</th>
                                <td>${data.first_in || '-'}</td>
                            </tr>
                            <tr>
                                <th>Last Out</th>
                                <td>${data.last_out || '-'}</td>
                            </tr>
                            <tr>
                                <th>Work Duration</th>
                                <td>${data.work_duration || '-'}</td>
                            </tr>
                        </table>
                    </div>
                    ${data.raw_records ? `
                        <h6 class="mt-3">Raw Records</h6>
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Time</th>
                                        <th>Type</th>
                                        <th>Source</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${data.raw_records.map(record => `
                                        <tr>
                                            <td>${record.time}</td>
                                            <td>
                                                <span class="badge ${record.type === 'IN' ? 'bg-success' : 'bg-danger'}">
                                                    ${record.type}${record.label || ''}
                                                </span>
                                            </td>
                                            <td>${record.source}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    ` : ''}
                `;
                modal.show();
            })
            .catch(error => {
                console.error('Error loading attendance details:', error);
                showError('Failed to load attendance details');
            });
    }

    // Function to show error message
    function showError(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.card-body').prepend(alertDiv);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    // Event listeners for filters
    const filters = [startDateInput, endDateInput, departmentSelect, statusSelect, searchInput];
    filters.forEach(filter => {
        if (filter) {
            filter.addEventListener('change', () => loadAttendanceLogs(1));
        }
    });

    // Initial load
    loadAttendanceLogs();
});
