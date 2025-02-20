import {
    getReportParameters,
    handleExportFormat,
    handleDateRangeChange,
    setDateRangeFromPreset,
    formatDate,
    showLoadingState,
    hideLoadingState,
    showError
} from './report_utils.js';

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
    document.getElementById('generateReport')?.addEventListener('click', generateReport);
    document.getElementById('dateRange')?.addEventListener('change', handleDateRangeChange);
    document.getElementById('exportFormat')?.addEventListener('change', (e) => handleExportFormat(e, { defaultReportType: 'attendance' }));
    document.getElementById('reportType')?.addEventListener('change', handleReportTypeChange);
    
    // Initialize date inputs with default values
    setDefaultDates();
});

function setDefaultDates() {
    const today = new Date();
    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    if (startDateInput) startDateInput.value = formatDate(firstDayOfMonth);
    if (endDateInput) endDateInput.value = formatDate(today);
}

async function generateReport() {
    const params = getReportParameters();
    showLoadingState();
    
    try {
        const reportType = document.getElementById('reportType')?.value || 'attendance';
        const searchParams = new URLSearchParams();
        
        // Add basic parameters
        searchParams.append('start_date', params.start_date);
        searchParams.append('end_date', params.end_date);
        
        // Add array parameters correctly
        if (params.departments) {
            params.departments.forEach(dept => searchParams.append('departments[]', dept));
        }
        if (params.employees) {
            params.employees.forEach(emp => searchParams.append('employees[]', emp));
        }
        if (params.status) {
            params.status.forEach(status => searchParams.append('status[]', status));
        }
        
        const response = await fetch(`/attendance/api/reports/${reportType}/?${searchParams.toString()}`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch report data');
        }
        
        const data = await response.json();
        updateReportUI(data, reportType);
    } catch (error) {
        console.error('Error generating report:', error);
        showError(error.message || 'Failed to generate report. Please try again.');
    } finally {
        hideLoadingState();
    }
}

function updateReportUI(data, reportType) {
    // Update summary cards with default values in case data is missing
    const summary = data.summary || { present: 0, absent: 0, late: 0, leave: 0 };
    
    const presentCount = document.getElementById('presentCount');
    const absentCount = document.getElementById('absentCount');
    const lateCount = document.getElementById('lateCount');
    const leaveCount = document.getElementById('leaveCount');
    
    if (presentCount) presentCount.textContent = summary.present || '0';
    if (absentCount) absentCount.textContent = summary.absent || '0';
    if (lateCount) lateCount.textContent = summary.late || '0';
    if (leaveCount) leaveCount.textContent = summary.leave || '0';
    
    // Display holidays if they exist
    const holidayInfo = document.getElementById('holidayInfo');
    if (holidayInfo && data.holidays && data.holidays.length > 0) {
        holidayInfo.innerHTML = `
            <div class="alert alert-info">
                <h5>Holidays in Selected Period:</h5>
                <ul class="list-unstyled mb-0">
                    ${data.holidays.map(holiday => 
                        `<li><strong>${formatDate(new Date(holiday.date))}:</strong> ${holiday.name}</li>`
                    ).join('')}
                </ul>
            </div>
        `;
        holidayInfo.style.display = 'block';
    } else if (holidayInfo) {
        holidayInfo.style.display = 'none';
    }
    
    // Update charts if data is available
    if (data.trend_data) {
        updateAttendanceTrendChart(data.trend_data);
    }
    if (data.department_stats) {
        updateDepartmentChart(data.department_stats);
    }
    
    // Update report table
    if (data.employee_records) {
        updateReportTable(data.employee_records);
    }
}

function updateReportTable(records) {
    const tbody = document.querySelector('#reportTable tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    records.forEach(record => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${record.id || ''}</td>
            <td>${record.name || ''}</td>
            <td>${record.department || ''}</td>
            <td>${record.present_days || 0}</td>
            <td>${record.absent_days || 0}</td>
            <td>${record.late_days || 0}</td>
            <td>${record.leave_days || 0}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="viewEmployeeDetails(${record.id})">
                    View Details
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function updateAttendanceTrendChart(trendData) {
    const ctx = document.getElementById('attendanceTrendChart')?.getContext('2d');
    if (!ctx) return;
    
    if (attendanceTrendChart) {
        attendanceTrendChart.destroy();
    }
    
    const labels = trendData.map(data => {
        const label = formatDate(new Date(data.date));
        return data.is_holiday ? `${label} (Holiday)` : label;
    });
    
    const datasets = [
        {
            label: 'Present',
            data: trendData.map(data => data.present),
            backgroundColor: CHART_COLORS.present,
            borderColor: CHART_COLORS.present,
            tension: 0.1
        },
        {
            label: 'Absent',
            data: trendData.map(data => data.absent),
            backgroundColor: CHART_COLORS.absent,
            borderColor: CHART_COLORS.absent,
            tension: 0.1
        },
        {
            label: 'Late',
            data: trendData.map(data => data.late),
            backgroundColor: CHART_COLORS.late,
            borderColor: CHART_COLORS.late,
            tension: 0.1
        },
        {
            label: 'Leave',
            data: trendData.map(data => data.leave),
            backgroundColor: CHART_COLORS.leave,
            borderColor: CHART_COLORS.leave,
            tension: 0.1
        }
    ];
    
    attendanceTrendChart = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                x: {
                    ticks: {
                        callback: function(value, index) {
                            const isHoliday = trendData[index]?.is_holiday;
                            const label = this.getLabelForValue(value);
                            return isHoliday ? `${label} *` : label;
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Daily Attendance Trend'
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const index = context[0].dataIndex;
                            const data = trendData[index];
                            let title = formatDate(new Date(data.date));
                            if (data.is_holiday) {
                                title += ` (Holiday - ${data.holiday_name})`;
                            }
                            return title;
                        }
                    }
                }
            }
        }
    });
}

function updateDepartmentChart(departmentStats) {
    const ctx = document.getElementById('departmentChart')?.getContext('2d');
    if (!ctx) return;
    
    if (departmentChart) {
        departmentChart.destroy();
    }
    
    const labels = departmentStats.map(stat => stat.department);
    const datasets = [
        {
            label: 'Present',
            data: departmentStats.map(stat => stat.present),
            backgroundColor: CHART_COLORS.present
        },
        {
            label: 'Absent',
            data: departmentStats.map(stat => stat.absent),
            backgroundColor: CHART_COLORS.absent
        },
        {
            label: 'Late',
            data: departmentStats.map(stat => stat.late),
            backgroundColor: CHART_COLORS.late
        },
        {
            label: 'Leave',
            data: departmentStats.map(stat => stat.leave),
            backgroundColor: CHART_COLORS.leave
        }
    ];
    
    departmentChart = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets },
        options: {
            responsive: true,
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Department-wise Attendance'
                }
            }
        }
    });
}

function viewEmployeeDetails(employeeId) {
    if (employeeId) {
        window.location.href = `/attendance/attendance_detail/?employee_id=${employeeId}`;
    }
}
