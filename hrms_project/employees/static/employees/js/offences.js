document.addEventListener('DOMContentLoaded', function() {
    const employeeId = 1; // Make sure this is defined globally
    const API_BASE = '/employees/api'; // Base API path

    // Initialize modals
    const addOffenceModal = new bootstrap.Modal('#addOffenceModal');
    const viewOffenceModal = new bootstrap.Modal('#viewOffenceModal');
    const addDocumentModal = new bootstrap.Modal('#addDocumentModal');

    // Handle offence type selection
    document.getElementById('offenceType').addEventListener('change', function() {
        const otherTypeDiv = document.getElementById('otherTypeDiv');
        const otherTypeInput = document.getElementById('otherType');
        
        if (this.value === 'OTHER') {
            otherTypeDiv.style.display = 'block';
            otherTypeInput.required = true;
        } else {
            otherTypeDiv.style.display = 'none';
            otherTypeInput.required = false;
            otherTypeInput.value = '';
        }
    });

    // Handle save offence
    document.getElementById('saveOffenceBtn').addEventListener('click', async function() {
        const form = document.getElementById('addOffenceForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Handle other type
        if (data.offence_type === 'OTHER' && data.other_type) {
            data.offence_type_other = data.other_type;
            delete data.other_type;
        }

        try {
            const response = await fetch(`/employees/${employeeId}/offences/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to add offence');
            }

            const newOffence = await response.json();
            addOffenceToTable(newOffence);
            
            // Reset and close modal
            form.reset();
            addOffenceModal.hide();
            
        } catch (error) {
            console.error('Error adding offence:', error);
            alert(error.message || 'Failed to add offence. Please try again.');
        }
    });

    // Handle view offence
    document.addEventListener('click', function(e) {
        const viewBtn = e.target.closest('.view-offence');
        if (viewBtn) {
            e.preventDefault();
            const offenceId = viewBtn.dataset.offenceId;
            viewOffence(offenceId);
        }
    });

    // Handle add document
    document.addEventListener('click', function(e) {
        const addDocBtn = e.target.closest('.add-document');
        if (addDocBtn) {
            e.preventDefault();
            const offenceId = addDocBtn.dataset.offenceId;
            document.getElementById('documentOffenceId').value = offenceId;
            addDocumentModal.show();
        }
    });

    // Handle save document
    document.getElementById('saveDocumentBtn').addEventListener('click', async function() {
        const form = document.getElementById('addDocumentForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const formData = new FormData(form);
        const offenceId = formData.get('offence_id');

        try {
            const response = await fetch(`/employees/${employeeId}/offences/${offenceId}/documents/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to upload document');
            }

            const newDocument = await response.json();
            
            // Reset and close modal
            form.reset();
            addDocumentModal.hide();
            
            // Refresh offence details if viewing
            const viewingOffenceId = document.querySelector('#viewOffenceModal').dataset.offenceId;
            if (viewingOffenceId === offenceId) {
                viewOffence(offenceId);
            }
            
        } catch (error) {
            console.error('Error uploading document:', error);
            alert(error.message || 'Failed to upload document. Please try again.');
        }
    });

    // Handle cancel offence
    document.addEventListener('click', function(e) {
        const cancelBtn = e.target.closest('.cancel-offence');
        if (cancelBtn) {
            e.preventDefault();
            const offenceId = cancelBtn.dataset.offenceId;
            if (confirm('Are you sure you want to cancel this offence? This cannot be undone.')) {
                cancelOffence(offenceId);
            }
        }
    });

    // Function to view offence details
    async function viewOffence(offenceId) {
        try {
            const response = await fetch(`/employees/${employeeId}/offences/${offenceId}/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch offence details');
            }

            const offence = await response.json();
            
            // Populate modal with offence details
            document.getElementById('viewRefNo').textContent = offence.ref_no;
            document.getElementById('viewEnteredOn').textContent = new Date(offence.entered_on).toLocaleDateString();
            document.getElementById('viewOffenceType').textContent = offence.offence_type_display;
            document.getElementById('viewTotalValue').textContent = offence.total_value;
            document.getElementById('viewDetails').textContent = offence.details;
            document.getElementById('viewStartDate').textContent = new Date(offence.start_date).toLocaleDateString();
            document.getElementById('viewEndDate').textContent = offence.end_date ? new Date(offence.end_date).toLocaleDateString() : '-';
            document.getElementById('viewStatus').textContent = offence.is_cancelled ? 'Cancelled' : 'Active';

            // Handle documents
            const documentsContainer = document.getElementById('viewDocuments');
            if (offence.documents && offence.documents.length > 0) {
                const documentsList = offence.documents.map(doc => `
                    <div class="mb-1">
                        <a href="${doc.file_url}" target="_blank">${doc.title}</a>
                    </div>
                `).join('');
                documentsContainer.innerHTML = documentsList;
            } else {
                documentsContainer.innerHTML = '<em>No documents attached</em>';
            }

            // Store offence ID in modal for reference
            document.querySelector('#viewOffenceModal').dataset.offenceId = offenceId;
            
            // Show the modal
            viewOffenceModal.show();
            
        } catch (error) {
            console.error('Error viewing offence:', error);
            alert(error.message || 'Failed to view offence details');
        }
    }

    // Function to cancel offence
    async function cancelOffence(offenceId) {
        try {
            const response = await fetch(`/employees/${employeeId}/offences/${offenceId}/cancel/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to cancel offence');
            }

            // Update the table row
            const row = document.querySelector(`tr[data-offence-id="${offenceId}"]`);
            if (row) {
                const statusCell = row.querySelector('td:nth-child(7)');
                const actionsCell = row.querySelector('td:nth-child(8)');
                
                statusCell.innerHTML = '<span class="badge bg-danger">Cancelled</span>';
                const cancelBtn = actionsCell.querySelector('.cancel-offence');
                if (cancelBtn) {
                    cancelBtn.remove();
                }
            }
            
        } catch (error) {
            console.error('Error cancelling offence:', error);
            alert(error.message || 'Failed to cancel offence');
        }
    }

    // Function to add new offence to table
    function addOffenceToTable(offence) {
        const tbody = document.querySelector('#offencesTable tbody');
        const noOffencesRow = tbody.querySelector('tr td[colspan="8"]')?.parentElement;
        if (noOffencesRow) {
            noOffencesRow.remove();
        }

        const newRow = document.createElement('tr');
        newRow.dataset.offenceId = offence.id;
        newRow.innerHTML = `
            <td>${offence.ref_no}</td>
            <td>${new Date(offence.entered_on).toLocaleDateString()}</td>
            <td>${offence.offence_type_display}</td>
            <td>${offence.total_value}</td>
            <td>${new Date(offence.start_date).toLocaleDateString()}</td>
            <td>${offence.end_date ? new Date(offence.end_date).toLocaleDateString() : '-'}</td>
            <td>
                <span class="badge bg-warning">Active</span>
            </td>
            <td>
                <button type="button" class="btn btn-sm btn-info view-offence" data-offence-id="${offence.id}" title="View Details">
                    <i class="fas fa-eye"></i>
                </button>
                <button type="button" class="btn btn-sm btn-primary add-document" data-offence-id="${offence.id}" title="Add Document">
                    <i class="fas fa-file-upload"></i>
                </button>
                <button type="button" class="btn btn-sm btn-danger cancel-offence" data-offence-id="${offence.id}" title="Cancel Offence">
                    <i class="fas fa-ban"></i>
                </button>
            </td>
        `;
        tbody.insertBefore(newRow, tbody.firstChild);
    }

    // Utility function to get CSRF token
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
});
