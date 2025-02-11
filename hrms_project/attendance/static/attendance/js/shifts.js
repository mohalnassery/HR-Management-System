// Function to check for overlapping shifts
async function checkOverlappingShifts() {
    const employeeId = document.getElementById('employee').value;
    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value || startDate;
    const currentAssignmentId = new URLSearchParams(window.location.search).get('id');

    try {
        const response = await fetch(`/api/attendance/check-shift-overlap/?employee=${employeeId}&start_date=${startDate}&end_date=${endDate}${currentAssignmentId ? `&exclude=${currentAssignmentId}` : ''}`);
        const data = await response.json();
        
        const warningElement = document.getElementById('overlap-warning');
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
                document.getElementById('shift-assignment-form').insertBefore(
                    warningDiv,
                    document.querySelector('.mb-3:last-child')
                );
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
    const selectedOption = shiftSelect.options[shiftSelect.selectedIndex];
    const nightShiftBadge = document.getElementById('night-shift-badge');
    
    // Get shift data from data attributes
    const isNightShift = selectedOption.dataset.isNightShift === 'true';
    
    if (isNightShift) {
        if (!nightShiftBadge) {
            const badge = document.createElement('span');
            badge.id = 'night-shift-badge';
            badge.className = 'badge bg-info ms-2';
            badge.innerHTML = '<i class="fas fa-moon"></i> Night Shift';
            shiftSelect.parentNode.appendChild(badge);
        }
    } else if (nightShiftBadge) {
        nightShiftBadge.remove();
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('shift-assignment-form');
    const employeeSelect = document.getElementById('employee');
    const shiftSelect = document.getElementById('shift');
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');

    // Initialize night shift indicator
    updateNightShiftIndicator();

    // Check for overlaps when form inputs change
    [employeeSelect, startDateInput, endDateInput].forEach(element => {
        element.addEventListener('change', checkOverlappingShifts);
    });

    // Update night shift indicator when shift selection changes
    shiftSelect.addEventListener('change', updateNightShiftIndicator);
});
