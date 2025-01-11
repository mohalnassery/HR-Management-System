document.addEventListener('DOMContentLoaded', function() {
    const employeeId = 1; // Make sure this is defined globally
    const API_BASE = '/employees/api'; // Base API path

    // Initialize modals
    const viewAssetModal = new bootstrap.Modal('#viewAssetModal');
    const assetsModal = new bootstrap.Modal(document.getElementById('addAssetsModal'));
    const assetTypeModal = new bootstrap.Modal(document.getElementById('addAssetTypeModal'));
    const manageTypesModal = new bootstrap.Modal(document.getElementById('manageAssetTypesModal'));
    const returnAssetModal = new bootstrap.Modal(document.getElementById('returnAssetModal'));

    // Function to properly clean up modal
    function cleanupModal() {
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }

    // Handle saving asset type
    document.getElementById('saveAssetTypeBtn').addEventListener('click', async function() {
        const formData = new FormData(document.getElementById('addAssetTypeForm'));
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch(`${API_BASE}/asset-types/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to add asset type');
            }

            const newType = await response.json();
            
            // Add new option to asset type select
            const select = document.querySelector('#addAssetsForm select[name="asset_type"]');
            const option = new Option(newType.name, newType.id);
            select.add(option);
            option.selected = true; // Select the new option

            // Add new row to asset types table if it exists
            const typeTable = document.querySelector('#assetTypesTable tbody');
            if (typeTable) {
                const newRow = typeTable.insertRow();
                newRow.dataset.typeId = newType.id;
                newRow.innerHTML = `
                    <td>${newType.name}</td>
                    <td>${newType.description || '-'}</td>
                    <td>
                        <button type="button" class="btn btn-sm btn-danger delete-type" data-type-id="${newType.id}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                `;
            }

            // Reset and close the asset type modal
            document.getElementById('addAssetTypeForm').reset();
            assetTypeModal.hide();
            cleanupModal();

        } catch (error) {
            console.error('Error adding asset type:', error);
            alert(error.message || 'Failed to add asset type. Please try again.');
        }
    });

    // Handle assets form submission
    document.getElementById('saveAssetsBtn').addEventListener('click', async function() {
        const form = document.getElementById('addAssetsForm');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        const selectedTypes = Array.from(form.querySelector('select[name="asset_type"]').selectedOptions);

        if (selectedTypes.length === 0) {
            alert('Please select at least one asset type');
            return;
        }

        try {
            let currentNumber = data.asset_number;

            for (const option of selectedTypes) {
                const type = {
                    id: option.value,
                    name: option.text
                };
                const quantity = parseInt(data[`quantity_${type.id}`]) || 1;

                for (let i = 0; i < quantity; i++) {
                    const assetData = {
                        asset_name: `${type.name} ${currentNumber}`,
                        asset_type_id: type.id,
                        asset_number: currentNumber,
                        issue_date: data.issue_date || new Date().toISOString().split('T')[0],
                        condition: data.condition || 'New',
                        value: data.value || '0',
                        notes: data.notes || ''
                    };

                    console.log('Sending asset data:', assetData);
                    const response = await fetch(`/employees/${employeeId}/assets/add/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify(assetData)
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.error || `Failed to add ${type.name} asset ${i + 1}`);
                    }

                    currentNumber = incrementAssetNumber(currentNumber, 1);
                }
            }

            // Reset form and close modal
            form.reset();
            assetsModal.hide();
            cleanupModal();
            location.reload();
        } catch (error) {
            console.error('Error adding assets:', error);
            alert(error.message || 'Failed to add assets. Please try again.');
        }
    });

    // Handle deleting asset type
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-type') || e.target.closest('.delete-type')) {
            const btn = e.target.classList.contains('delete-type') ? e.target : e.target.closest('.delete-type');
            const typeId = btn.dataset.typeId;
            const typeName = btn.closest('tr').cells[0].textContent;

            if (confirm(`Are you sure you want to delete the asset type "${typeName}"? This cannot be undone.`)) {
                deleteAssetType(typeId);
            }
        }
    });

    // Function to delete asset type
    async function deleteAssetType(typeId) {
        try {
            const response = await fetch(`${API_BASE}/asset-types/${typeId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to delete asset type');
            }

            // Remove the row from the manage types table
            const row = document.querySelector(`#assetTypesTable tr[data-type-id="${typeId}"]`);
            if (row) {
                row.remove();
            }

            // Remove the option from the asset type select
            const select = document.querySelector('#addAssetsForm select[name="asset_type"]');
            const option = select.querySelector(`option[value="${typeId}"]`);
            if (option) {
                option.remove();
            }

        } catch (error) {
            console.error('Error deleting asset type:', error);
            alert(error.message || 'Failed to delete asset type. Please try again.');
        }
    }

    // Handle view asset button
    document.addEventListener('click', function(e) {
        const viewBtn = e.target.closest('.view-asset');
        if (viewBtn) {
            e.preventDefault();
            const assetId = viewBtn.dataset.assetId;
            viewAsset(assetId);
        }
    });

    // Function to view asset details
    async function viewAsset(assetId) {
        try {
            const response = await fetch(`/employees/${employeeId}/assets/${assetId}/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch asset details');
            }

            const asset = await response.json();
            console.log('Asset details:', asset); // Debug log
            
            // Populate modal with asset details
            const elements = {
                viewAssetType: asset.asset_type?.name,
                viewAssetName: asset.asset_name,
                viewAssetNumber: asset.asset_number,
                viewIssueDate: asset.issue_date ? new Date(asset.issue_date).toLocaleDateString() : null,
                viewCondition: asset.condition,
                viewValue: asset.value ? `$${parseFloat(asset.value).toFixed(2)}` : null,
                viewNotes: asset.notes
            };

            // Update each element with fallback to '-' if value is null/undefined
            Object.entries(elements).forEach(([id, value]) => {
                const element = document.getElementById(id);
                if (element) {
                    element.textContent = value || '-';
                }
            });

            // Handle return details section
            const returnSection = document.getElementById('returnDetailsSection');
            if (returnSection) {
                if (asset.return_date) {
                    document.getElementById('viewReturnDate').textContent = new Date(asset.return_date).toLocaleDateString();
                    document.getElementById('viewReturnCondition').textContent = asset.return_condition || '-';
                    document.getElementById('viewReturnNotes').textContent = asset.return_notes || '-';
                    returnSection.style.display = 'block';
                } else {
                    returnSection.style.display = 'none';
                }
            }

            // Show the modal
            const modalElement = document.getElementById('viewAssetModal');
            if (modalElement) {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
            }
            
        } catch (error) {
            console.error('Error viewing asset:', error);
            alert(error.message || 'Failed to view asset details');
        }
    }

    // Handle return asset button
    document.addEventListener('click', function(e) {
        if (e.target.closest('.return-asset')) {
            const btn = e.target.closest('.return-asset');
            const assetId = btn.dataset.assetId;
            const row = btn.closest('tr');
            const assetName = row.cells[2].textContent;
            
            // Set current date as default
            const returnDateInput = document.getElementById('returnDate');
            returnDateInput.value = new Date().toISOString().split('T')[0];
            
            // Store asset ID in the modal
            document.getElementById('returnAssetIds').value = assetId;
            
            // Show return modal
            returnAssetModal.show();
        }
    });

    // Handle select all checkbox
    document.getElementById('selectAll').addEventListener('change', function(e) {
        const checkboxes = document.querySelectorAll('.asset-select:not(:disabled)');
        checkboxes.forEach(checkbox => checkbox.checked = e.target.checked);
        updateBulkReturnButton();
    });

    // Handle individual checkboxes
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('asset-select')) {
            updateBulkReturnButton();
        }
    });

    // Update bulk return button visibility
    function updateBulkReturnButton() {
        const checkedBoxes = document.querySelectorAll('.asset-select:checked').length;
        const bulkReturnBtn = document.getElementById('bulkReturnBtn');
        bulkReturnBtn.style.display = checkedBoxes > 0 ? 'inline-block' : 'none';
    }

    // Handle bulk return button
    document.getElementById('bulkReturnBtn').addEventListener('click', function() {
        const selectedAssets = Array.from(document.querySelectorAll('.asset-select:checked')).map(checkbox => {
            const row = checkbox.closest('tr');
            return {
                id: row.dataset.assetId,
                name: row.cells[2].textContent
            };
        });

        if (selectedAssets.length === 0) {
            alert('Please select at least one asset to return');
            return;
        }

        // Set current date as default
        const returnDateInput = document.getElementById('returnDate');
        returnDateInput.value = new Date().toISOString().split('T')[0];
        
        // Store asset IDs in the modal
        document.getElementById('returnAssetIds').value = selectedAssets.map(a => a.id).join(',');
        
        // Show return modal
        returnAssetModal.show();
    });

    // Handle confirm return button
    document.getElementById('confirmReturnAsset').addEventListener('click', async function() {
        const form = document.getElementById('returnAssetForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const assetIds = document.getElementById('returnAssetIds').value.split(',');
        const returnDate = document.getElementById('returnDate').value;
        const returnCondition = document.getElementById('returnCondition').value;
        const returnNotes = document.getElementById('returnNotes').value;

        try {
            // Return each asset
            for (const assetId of assetIds) {
                const response = await fetch(`/employees/${employeeId}/assets/${assetId}/return/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        return_date: returnDate,
                        return_condition: returnCondition,
                        return_notes: returnNotes
                    })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to return asset');
                }
            }

            // Close modal and refresh page
            returnAssetModal.hide();
            cleanupModal();
            location.reload();
            
        } catch (error) {
            console.error('Error returning assets:', error);
            alert(error.message || 'Failed to return assets');
        }
    });

    // Handle delete asset button
    document.addEventListener('click', function(e) {
        if (e.target.closest('.delete-asset')) {
            const btn = e.target.closest('.delete-asset');
            const assetId = btn.dataset.assetId;
            const row = btn.closest('tr');
            const assetName = row.cells[2].textContent;
            
            if (confirm(`Are you sure you want to delete "${assetName}"? This cannot be undone.`)) {
                deleteAsset(assetId);
            }
        }
    });

    // Function to delete an asset
    async function deleteAsset(assetId) {
        try {
            const response = await fetch(`/employees/${employeeId}/assets/${assetId}/delete/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            if (!response.ok) {
                throw new Error('Failed to delete asset');
            }

            // Remove the row from the table
            const row = document.querySelector(`tr[data-asset-id="${assetId}"]`);
            if (row) {
                row.remove();
            }
            
        } catch (error) {
            console.error('Error deleting asset:', error);
            alert(error.message || 'Failed to delete asset');
        }
    }

    // Utility function to increment asset numbers
    function incrementAssetNumber(baseNumber, increment) {
        const matches = baseNumber.match(/^([A-Za-z]+)(\d+)$/);
        if (!matches) return baseNumber;
        
        const prefix = matches[1];
        const number = parseInt(matches[2]);
        const newNumber = (number + increment).toString().padStart(matches[2].length, '0');
        return prefix + newNumber;
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

    // Add event listeners for modal hidden events
    ['addAssetTypeModal', 'manageAssetTypesModal', 'addAssetsModal', 'viewAssetModal', 'returnAssetModal'].forEach(modalId => {
        const modalElement = document.getElementById(modalId);
        if (modalElement) {
            modalElement.addEventListener('hidden.bs.modal', cleanupModal);
        }
    });

    // Handle modal backdrop cleanup
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            cleanupModal();
        }
    });
});
