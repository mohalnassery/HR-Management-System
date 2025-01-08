document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    const assetsTable = document.getElementById('assetsTable');
    const selectAllCheckbox = document.getElementById('selectAll');
    const bulkReturnBtn = document.getElementById('bulkReturnBtn');
    const addAssetForm = document.getElementById('addAssetForm');
    const returnAssetForm = document.getElementById('returnAssetForm');
    const addAssetTypeForm = document.getElementById('addAssetTypeForm');
    const assetTypeSelect = document.getElementById('assetTypeSelect');
    
    // Handle select all checkbox
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.asset-select:not([disabled])');
            checkboxes.forEach(checkbox => {
                checkbox.checked = selectAllCheckbox.checked;
            });
            updateBulkReturnButton();
        });
    }

    // Handle individual checkboxes
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('asset-select')) {
            updateBulkReturnButton();
        }
    });

    // Update bulk return button visibility
    function updateBulkReturnButton() {
        const checkedBoxes = document.querySelectorAll('.asset-select:checked').length;
        bulkReturnBtn.style.display = checkedBoxes > 0 ? 'inline-block' : 'none';
    }

    // Handle bulk return
    if (bulkReturnBtn) {
        bulkReturnBtn.addEventListener('click', function() {
            const selectedAssets = Array.from(document.querySelectorAll('.asset-select:checked')).map(checkbox => {
                return checkbox.closest('tr').dataset.assetId;
            });
            
            if (selectedAssets.length > 0) {
                const returnModal = new bootstrap.Modal(document.getElementById('returnAssetModal'));
                returnModal.show();
                
                // Store selected assets in the form for later use
                returnAssetForm.dataset.selectedAssets = JSON.stringify(selectedAssets);
            }
        });
    }

    // Handle individual return
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('return-asset') || e.target.closest('.return-asset')) {
            const btn = e.target.classList.contains('return-asset') ? e.target : e.target.closest('.return-asset');
            const assetId = btn.dataset.assetId;
            
            const returnModal = new bootstrap.Modal(document.getElementById('returnAssetModal'));
            returnAssetForm.dataset.selectedAssets = JSON.stringify([assetId]);
            returnModal.show();
        }
    });

    // Handle "Set Current Date/Time" button
    document.getElementById('setCurrentDateTimeBtn').addEventListener('click', function() {
        const today = new Date().toISOString().split('T')[0];
        document.querySelector('input[name="return_date"]').value = today;
    });

    // Handle asset return submission
    document.getElementById('confirmReturnBtn').addEventListener('click', async function() {
        const selectedAssets = JSON.parse(returnAssetForm.dataset.selectedAssets || '[]');
        const returnDate = returnAssetForm.querySelector('input[name="return_date"]').value;
        const returnCondition = returnAssetForm.querySelector('textarea[name="return_condition"]').value;

        if (!returnDate || !returnCondition) {
            alert('Please fill in all required fields');
            return;
        }

        try {
            const response = await fetch('/employees/api/return-assets/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    asset_ids: selectedAssets,
                    return_date: returnDate,
                    return_condition: returnCondition
                })
            });

            if (response.ok) {
                location.reload();
            } else {
                throw new Error('Failed to return assets');
            }
        } catch (error) {
            console.error('Error returning assets:', error);
            alert('Failed to return assets. Please try again.');
        }
    });

    // Handle new asset type submission
    document.getElementById('saveAssetTypeBtn').addEventListener('click', async function() {
        const formData = new FormData(addAssetTypeForm);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch('/employees/api/asset-types/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                const newType = await response.json();
                // Add new option to select
                const option = new Option(newType.name, newType.id);
                assetTypeSelect.add(option);
                // Select the new option
                assetTypeSelect.value = newType.id;
                // Close the modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('addAssetTypeModal'));
                modal.hide();
                // Clear the form
                addAssetTypeForm.reset();
            } else {
                throw new Error('Failed to add asset type');
            }
        } catch (error) {
            console.error('Error adding asset type:', error);
            alert('Failed to add asset type. Please try again.');
        }
    });

    // Handle asset deletion
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-asset') || e.target.closest('.delete-asset')) {
            const btn = e.target.classList.contains('delete-asset') ? e.target : e.target.closest('.delete-asset');
            const assetId = btn.dataset.assetId;
            
            if (confirm('Are you sure you want to delete this asset?')) {
                deleteAsset(assetId);
            }
        }
    });

    // Handle asset view/edit
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('view-asset') || e.target.closest('.view-asset')) {
            const btn = e.target.classList.contains('view-asset') ? e.target : e.target.closest('.view-asset');
            const assetId = btn.dataset.assetId;
            viewAsset(assetId);
        }
    });

    // Handle new asset form submission
    document.getElementById('saveAssetBtn').addEventListener('click', async function() {
        const formData = new FormData(addAssetForm);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch('/employees/api/assets/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                location.reload();
            } else {
                throw new Error('Failed to add asset');
            }
        } catch (error) {
            console.error('Error adding asset:', error);
            alert('Failed to add asset. Please try again.');
        }
    });

    // Utility functions
    async function deleteAsset(assetId) {
        try {
            const response = await fetch(`/employees/api/assets/${assetId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            if (response.ok) {
                location.reload();
            } else {
                throw new Error('Failed to delete asset');
            }
        } catch (error) {
            console.error('Error deleting asset:', error);
            alert('Failed to delete asset. Please try again.');
        }
    }

    async function viewAsset(assetId) {
        try {
            const response = await fetch(`/employees/api/assets/${assetId}/`);
            const asset = await response.json();

            const modalBody = document.querySelector('#viewAssetModal .modal-body');
            modalBody.innerHTML = `
                <div class="mb-3">
                    <strong>Asset Type:</strong> ${asset.asset_type.name}
                </div>
                <div class="mb-3">
                    <strong>Asset Name:</strong> ${asset.asset_name}
                </div>
                <div class="mb-3">
                    <strong>Asset Number:</strong> ${asset.asset_number}
                </div>
                <div class="mb-3">
                    <strong>Issue Date:</strong> ${asset.issue_date}
                </div>
                <div class="mb-3">
                    <strong>Return Date:</strong> ${asset.return_date || 'Not returned'}
                </div>
                <div class="mb-3">
                    <strong>Condition:</strong> ${asset.condition}
                </div>
                <div class="mb-3">
                    <strong>Value:</strong> ${asset.value}
                </div>
                ${asset.notes ? `
                <div class="mb-3">
                    <strong>Notes:</strong> ${asset.notes}
                </div>
                ` : ''}
                ${asset.return_date ? `
                <div class="mb-3">
                    <strong>Return Condition:</strong> ${asset.return_condition || 'N/A'}
                </div>
                ` : ''}
            `;

            const viewModal = new bootstrap.Modal(document.getElementById('viewAssetModal'));
            viewModal.show();
        } catch (error) {
            console.error('Error viewing asset:', error);
            alert('Failed to load asset details. Please try again.');
        }
    }

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
