// Utility Functions
function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatTime(time) {
    if (!time) return '-';
    return new Date(`2000-01-01T${time}`).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
}

function calculateDuration(startDate, endDate, startHalf = false, endHalf = false) {
    const days = Math.ceil((new Date(endDate) - new Date(startDate)) / (1000 * 60 * 60 * 24)) + 1;
    let deductions = 0;
    if (startHalf) deductions += 0.5;
    if (endHalf) deductions += 0.5;
    return days - deductions;
}

// Toast Notifications
function showToast(message, type = 'success') {
    const toastHtml = `
        <div class="position-fixed bottom-0 end-0 p-3" style="z-index: 1050">
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', toastHtml);
    const toast = document.querySelector('.toast:last-child');
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast from DOM after it's hidden
    toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

// Form Validation
function validateDateRange(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    return start <= end;
}

function validateFileSize(file, maxSize = 5) {
    // maxSize in MB
    return file.size <= maxSize * 1024 * 1024;
}

function validateFileType(file, allowedTypes = ['pdf', 'jpg', 'jpeg', 'png']) {
    const extension = file.name.split('.').pop().toLowerCase();
    return allowedTypes.includes(extension);
}

// AJAX Helpers
function sendRequest(url, method = 'GET', data = null, options = {}) {
    const defaultOptions = {
        method: method,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            ...options.headers
        }
    };

    if (data) {
        if (data instanceof FormData) {
            defaultOptions.body = data;
        } else {
            defaultOptions.headers['Content-Type'] = 'application/json';
            defaultOptions.body = JSON.stringify(data);
        }
    }

    return fetch(url, { ...defaultOptions, ...options })
        .then(response => {
            if (!response.ok) {
                return response.json().then(json => Promise.reject(json));
            }
            return response.json();
        });
}

// Attendance Status Handling
const STATUS_COLORS = {
    'Present': 'success',
    'Absent': 'danger',
    'Late': 'warning',
    'Leave': 'info',
    'Holiday': 'primary'
};

function getStatusBadge(status) {
    const color = STATUS_COLORS[status] || 'secondary';
    return `<span class="badge bg-${color}">${status}</span>`;
}

// Calendar Event Helpers
function getEventColor(type, status) {
    if (type === 'holiday') return '#0d6efd';  // primary
    if (type === 'leave') return '#0dcaf0';    // info
    
    switch (status) {
        case 'Present': return '#198754';  // success
        case 'Absent': return '#dc3545';   // danger
        case 'Late': return '#ffc107';     // warning
        default: return '#6c757d';         // secondary
    }
}

// Form Handling
function initializeLeaveForm() {
    const leaveType = document.getElementById('leave_type');
    const startDate = document.getElementById('start_date');
    const endDate = document.getElementById('end_date');
    const startHalf = document.getElementById('start_half');
    const endHalf = document.getElementById('end_half');
    const submitBtn = document.querySelector('button[type="submit"]');

    function updateDuration() {
        if (startDate.value && endDate.value) {
            const duration = calculateDuration(
                startDate.value,
                endDate.value,
                startHalf.checked,
                endHalf.checked
            );
            document.getElementById('duration-info').textContent = 
                `Duration: ${duration} day${duration !== 1 ? 's' : ''}`;
        }
    }

    [startDate, endDate, startHalf, endHalf].forEach(el => 
        el.addEventListener('change', updateDuration)
    );

    leaveType.addEventListener('change', function() {
        const requiresDoc = this.options[this.selectedIndex].dataset.requiresDocument === 'true';
        const docSection = document.getElementById('document-section');
        if (docSection) {
            docSection.style.display = requiresDoc ? 'block' : 'none';
            const docInput = docSection.querySelector('input[type="file"]');
            docInput.required = requiresDoc;
        }
    });
}

// Document Preview
function initializeDocumentPreview() {
    const input = document.querySelector('input[type="file"]');
    const preview = document.getElementById('document-preview');
    
    if (input && preview) {
        input.addEventListener('change', function() {
            preview.innerHTML = '';
            
            [...this.files].forEach(file => {
                if (!validateFileType(file) || !validateFileSize(file)) {
                    showToast('Invalid file type or size', 'danger');
                    return;
                }
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    const div = document.createElement('div');
                    div.className = 'mb-2';
                    
                    if (file.type.startsWith('image/')) {
                        div.innerHTML = `
                            <img src="${e.target.result}" class="img-thumbnail" style="max-height: 200px">
                            <div class="small text-muted mt-1">${file.name}</div>
                        `;
                    } else {
                        div.innerHTML = `
                            <div class="p-2 border rounded">
                                <i class="fas fa-file-pdf"></i> ${file.name}
                            </div>
                        `;
                    }
                    preview.appendChild(div);
                };
                reader.readAsDataURL(file);
            });
        });
    }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize any forms
    if (document.querySelector('form.needs-validation')) {
        initializeLeaveForm();
    }
    
    // Initialize document preview
    if (document.querySelector('input[type="file"]')) {
        initializeDocumentPreview();
    }
    
    // Initialize all tooltips
    var tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltips.map(function (tooltip) {
        return new bootstrap.Tooltip(tooltip);
    });
});
