/**
 * Common utilities for report handling
 */

// Report parameter handling
export function getReportParameters() {
    const params = {
        start_date: document.getElementById('startDate')?.value,
        end_date: document.getElementById('endDate')?.value
    };

    // Get department value
    const departmentSelect = document.getElementById('department');
    if (departmentSelect?.value) {
        params.departments = [departmentSelect.value];
    }

    // Get status values - handle multiple selection
    const statusSelect = document.getElementById('status');
    if (statusSelect?.selectedOptions) {
        const selectedStatus = Array.from(statusSelect.selectedOptions).map(opt => opt.value);
        if (selectedStatus.length > 0) {
            params.status = selectedStatus;
        }
    }

    const dateRange = document.getElementById('dateRange')?.value;
    if (dateRange && dateRange !== 'custom') {
        const dates = calculateDatesFromRange(dateRange);
        params.start_date = dates.startDate;
        params.end_date = dates.endDate;
    }
    
    return params;
}

// Export format handling
export async function handleExportFormat(event, options = {}) {
    const format = event.target.value;
    if (format === 'html') return;
    
    const reportType = document.getElementById('reportType')?.value || options.defaultReportType || 'attendance';
    const params = getReportParameters();
    const searchParams = new URLSearchParams();
    
    // Add all parameters
    Object.entries(params).forEach(([key, value]) => {
        if (Array.isArray(value)) {
            value.forEach(v => searchParams.append(`${key}[]`, v));
        } else {
            searchParams.append(key, value);
        }
    });
    
    // Add export format and type
    searchParams.append('format', format);
    searchParams.append('type', reportType);
    
    try {
        showLoadingState();
        if (format === 'pdf') {
            const response = await fetch(`/attendance/api/reports/export/?${searchParams.toString()}`);
            if (!response.ok) throw new Error('Failed to generate PDF');
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${reportType}_report.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } else {
            window.location.href = `/attendance/api/reports/export/?${searchParams.toString()}`;
        }
    } catch (error) {
        console.error('Error exporting report:', error);
        showError('Failed to export report. Please try again.');
    } finally {
        hideLoadingState();
        event.target.value = 'html';
    }
}

// Date handling utilities
export function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

export function calculateDatesFromRange(range) {
    const today = new Date();
    let startDate = new Date();
    
    switch (range) {
        case 'today':
            startDate = today;
            break;
        case 'week':
            startDate = new Date(today.setDate(today.getDate() - 7));
            break;
        case 'month':
            startDate = new Date(today.getFullYear(), today.getMonth(), 1);
            break;
    }
    
    return {
        startDate: formatDate(startDate),
        endDate: formatDate(new Date())
    };
}

// UI state handling
export function showLoadingState() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.add('active');
}

export function hideLoadingState() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.remove('active');
}

export function showError(message) {
    const errorToast = document.getElementById('errorToast');
    const errorMessage = document.getElementById('errorMessage');
    if (errorToast && errorMessage) {
        errorMessage.textContent = message;
        const toast = new bootstrap.Toast(errorToast);
        toast.show();
    } else {
        alert(message); // Fallback if toast elements don't exist
    }
}

// Date range handling
export function handleDateRangeChange(event) {
    const customDateRange = document.getElementById('customDateRange');
    if (customDateRange) {
        customDateRange.style.display = event.target.value === 'custom' ? 'block' : 'none';
    }
    
    if (event.target.value !== 'custom') {
        setDateRangeFromPreset(event.target.value);
    }
}

export function setDateRangeFromPreset(preset) {
    const today = new Date();
    let startDate = new Date();
    
    switch (preset) {
        case 'today':
            startDate = today;
            break;
        case 'week':
            startDate = new Date(today.setDate(today.getDate() - 7));
            break;
        case 'month':
            startDate = new Date(today.getFullYear(), today.getMonth(), 1);
            break;
    }
    
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    if (startDateInput) startDateInput.value = formatDate(startDate);
    if (endDateInput) endDateInput.value = formatDate(new Date());
}