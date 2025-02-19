// Constants
const CHART_COLORS = {
    present: 'rgb(40, 167, 69)',
    absent: 'rgb(220, 53, 69)',
    late: 'rgb(255, 193, 7)',
    leave: 'rgb(23, 162, 184)'
};

// State management
let attendanceTrendChart = null;
let departmentChart = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize event listeners
    document.getElementById('generateReport').addEventListener('click', generateReport);
    document.getElementById('dateRange').addEventListener('change', handleDateRangeChange);
    document.getElementById('exportFormat').addEventListener('change', handleExportFormat);
    document.getElementById('reportType').addEventListener('change', handleReportTypeChange);
    
    // Initialize date inputs with default values
    setDefaultDates();
});

function setDefaultDates() {
    const today = new Date();
    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    
    document.getElementById('startDate').value = formatDate(firstDayOfMonth);
    document.getElementById('endDate').value = formatDate(today);
}

function handleDateRangeChange(event) {
    const customDateRange = document.getElementById('customDateRange');
    customDateRange.style.display = event.target.value === 'custom' ? 'block' : 'none';
    
    if (event.target.value !== 'custom') {
        setDateRangeFromPreset(event.target.value);
    }
}

function handleReportTypeChange(event) {
    const reportType = event.target.value;
    // Update available export formats based on report type
    const exportFormat = document.getElementById('exportFormat');
    exportFormat.innerHTML = `
        <option value="html">Web View</option>
        <option value="csv">CSV</option>
        <option value="excel">Excel</option>
        <option value="pdf">PDF</option>
        ${reportType === 'attendance' ? '<option value="json">JSON</option>' : ''}
    `;
}

function setDateRangeFromPreset(preset) {
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
    
    document.getElementById('startDate').value = formatDate(startDate);
    document.getElementById('endDate').value = formatDate(new Date());
}

async function generateReport() {
    const params = getReportParameters();
    showLoadingState();
    
    try {
        const reportType = document.getElementById('reportType').value;
        const response = await fetch(`/attendance/api/reports/${reportType}/?${new URLSearchParams(params)}`);
        if (!response.ok) throw new Error('Failed to fetch report data');
        
        const data = await response.json();
        updateReportUI(data, reportType);
    } catch (error) {
        console.error('Error generating report:', error);
        showError('Failed to generate report. Please try again.');
    } finally {
        hideLoadingState();
    }
}

function getReportParameters() {
    const dateRange = document.getElementById('dateRange').value;
    const params = {
        departments: Array.from(document.getElementById('department').selectedOptions).map(opt => opt.value),
        start_date: document.getElementById('startDate').value,
        end_date: document.getElementById('endDate').value
    };
    
    if (dateRange !== 'custom') {
        const dates = calculateDatesFromRange(dateRange);
        params.start_date = dates.startDate;
        params.end_date = dates.endDate;
    }
    
    // Add status filters if selected
    const statusFilters = Array.from(document.getElementById('status').selectedOptions).map(opt => opt.value);
    if (statusFilters.length > 0) {
        params.status = statusFilters;
    }
    
    return params;
}

async function handleExportFormat(event) {
    const format = event.target.value;
    if (format === 'html') return;
    
    const reportType = document.getElementById('reportType').value;
    const params = {
        ...getReportParameters(),
        format: format,
        type: reportType
    };
    
    try {
        showLoadingState();
        if (format === 'pdf') {
            // For PDF, we need to handle the response differently
            const response = await fetch(`/attendance/api/reports/export/?${new URLSearchParams(params)}`);
            if (!response.ok) throw new Error('Failed to generate PDF');
            
            // Create blob from response and download
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
            // For other formats, use regular download
            window.location.href = `/attendance/api/reports/export/?${new URLSearchParams(params)}`;
        }
    } catch (error) {
        console.error('Error exporting report:', error);
        showError('Failed to export report. Please try again.');
    } finally {
        hideLoadingState();
        // Reset select to HTML view
        event.target.value = 'html';
    }
}

function updateReportUI(data, reportType) {
    switch (reportType) {
        case 'attendance':
            updateAttendanceReport(data);
            break;
        case 'leave':
            updateLeaveReport(data);
            break;
        case 'holiday':
            updateHolidayReport(data);
            break;
    }
}

function updateAttendanceReport(data) {
    // Update summary cards
    updateSummaryCards(data.summary);
    
    // Update charts
    updateAttendanceTrendChart(data.trend_data);
    updateDepartmentChart(data.department_stats);
    
    // Update detailed report table
    updateReportTable(data.employee_records);
}

function updateLeaveReport(data) {
    // Update summary stats
    document.getElementById('presentCount').textContent = data.total_leaves;
    document.getElementById('absentCount').textContent = data.approved_leaves;
    document.getElementById('lateCount').textContent = data.pending_leaves;
    document.getElementById('leaveCount').textContent = data.rejected_leaves;
    
    // Update charts with leave type distribution
    if (data.leave_type_stats) {
        updateLeaveTypeChart(data.leave_type_stats);
    }
    
    // Update detailed table
    updateLeaveTable(data.employee_records);
}

function updateHolidayReport(data) {
    // Update summary
    document.getElementById('presentCount').textContent = data.total_holidays;
    
    // Update holiday calendar
    updateHolidayCalendar(data.holidays);
}

// ... (keep existing chart and table update functions) ...

function showLoadingState() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.add('active');
}

function hideLoadingState() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.remove('active');
}

function showError(message) {
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

// Utility functions
function formatDate(date) {
    return date.toISOString().split('T')[0];
}

function calculateDatesFromRange(range) {
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
