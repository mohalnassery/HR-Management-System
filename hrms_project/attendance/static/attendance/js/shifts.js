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

// Add these functions at the top of the file

function initializeEmployeeSearch() {
    const searchInput = document.getElementById('modalEmployeeSearch');
    const modalEmployeeList = document.getElementById('modalEmployeeList');
    const modalDepartmentFilter = document.getElementById('modalDepartmentFilter');
    let searchTimeout;

    if (!searchInput || !modalEmployeeList) return;

    // Employee search functionality
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            modalEmployeeList.innerHTML = ''; // Clear results if query is too short
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
    if (modalDepartmentFilter) {
        modalDepartmentFilter.addEventListener('change', function() {
            const department = this.value;
            document.querySelectorAll('#modalEmployeeList .employee-item').forEach(item => {
                const empDepartment = item.dataset.department;
                item.style.display = (!department || empDepartment === department) ? '' : 'none';
            });
        });
    }

    // Handle employee selection confirmation
    const confirmButton = document.getElementById('confirmEmployeeSelection');
    if (confirmButton) {
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
                
                // Update calendar or handle the selection as needed
                calendar.refetchEvents();
            }

            // Close the modal
            bootstrap.Modal.getInstance(document.getElementById('employeeSearchModal')).hide();
        });
    }
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
                // Build query parameters
                const params = new URLSearchParams({
                    start: info.startStr,
                    end: info.endStr
                });
                
                if (selectedEmployeeId) {
                    params.append('employee_id', selectedEmployeeId);
                }
                if (departmentFilter.value) {
                    params.append('department_id', departmentFilter.value);
                }
                if (shiftTypeFilter.value) {
                    params.append('shift_type', shiftTypeFilter.value);
                }
                
                // Fetch events
                fetch(`/attendance/api/shift_assignment_calendar_events/?${params}`)
                    .then(response => response.json())
                    .then(data => {
                        successCallback(data);
                    })
                    .catch(error => {
                        console.error('Error:', error);
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
                // Show employee search modal when clicking on a date
                const modal = new bootstrap.Modal(document.getElementById('employeeSearchModal'));
                document.getElementById('selectedDate').value = info.dateStr;
                modal.show();
            }
        });

        // Fix calendar rendering on tab change
        document.querySelector('button[data-bs-target="#calendar-view"]').addEventListener('shown.bs.tab', function (e) {
            setTimeout(() => calendar.render(), 0);
        });

        calendar.render();

        // Handle filter changes
        departmentFilter?.addEventListener('change', () => calendar.refetchEvents());
        shiftTypeFilter?.addEventListener('change', () => calendar.refetchEvents());

        // Employee Search Functionality
        let searchTimeout;
        searchInput?.addEventListener('input', function() {
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
                        searchResults.innerHTML = data.map(emp => `
                            <div class="employee-item" data-id="${emp.id}" data-name="${emp.name}" data-number="${emp.employee_number}">
                                ${emp.name} (${emp.employee_number})
                            </div>
                        `).join('');
                        searchResults.classList.add('show');
                    });
            }, 300);
        });

        // Handle employee selection
        searchResults?.addEventListener('click', function(e) {
            const item = e.target.closest('.employee-item');
            if (item) {
                selectedEmployeeId = item.dataset.id;
                selectedEmployeeDiv.innerHTML = `
                    <div class="selected-employee">
                        <span>${item.dataset.name} (${item.dataset.number})</span>
                        <button type="button" class="btn btn-sm btn-outline-danger" id="removeEmployee">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                `;
                searchInput.value = '';
                searchResults.classList.remove('show');
                calendar.refetchEvents();
            }
        });

        // Handle remove employee
        document.getElementById('clearEmployee')?.addEventListener('click', function() {
            selectedEmployeeId = null;
            selectedEmployeeDiv.innerHTML = '';
            searchInput.value = '';
            calendar.refetchEvents();
        });

        // Close search results when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.employee-search')) {
                searchResults?.classList.remove('show');
            }
        });
    }

    // Initialize employee search in modal
    initializeEmployeeSearch();

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
