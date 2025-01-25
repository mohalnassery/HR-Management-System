// Global variables
let allRules = []; // Store all rules for searching

document.addEventListener('DOMContentLoaded', function() {
    // Initialize modals and tooltips
    const addOffenceModal = new bootstrap.Modal('#addOffenceModal');
    const viewOffenceModal = new bootstrap.Modal('#viewOffenceModal');
    const addDocumentModal = new bootstrap.Modal('#addDocumentModal');
    
    // Cache DOM elements
    const offenseSearch = document.getElementById('offenseSearch');
    const offenceGroup = document.getElementById('offenceGroup');
    const offenceRule = document.getElementById('offenceRule');
    const appliedPenalty = document.getElementById('appliedPenalty');
    const offenseDate = document.getElementById('offenseDate');
    const addOffenceForm = document.getElementById('addOffenceForm');
    const addDocumentForm = document.getElementById('addDocumentForm');
    const ruleDescription = document.getElementById('ruleDescription');
    const ruleDescriptionText = document.getElementById('ruleDescriptionText');
    const previousOffenses = document.getElementById('previousOffenses');
    const previousOffensesList = document.getElementById('previousOffensesList');
    const offenseYear = document.getElementById('offenseYear');
    const offenseCount = document.getElementById('offenseCount');
    const suggestedPenalty = document.getElementById('suggestedPenalty');
    const penaltyNote = document.getElementById('penaltyNote');
    const monetaryPenaltySection = document.getElementById('monetaryPenaltySection');

    let currentRule = null; // Store the currently selected rule

    // Get the employee ID from the URL
    const employeeId = window.location.pathname.split('/')[2];

    // Set default date to today
    const today = new Date().toISOString().split('T')[0];
    offenseDate.value = today;
    offenseYear.textContent = new Date().getFullYear();

    // Helper Functions
    function populateRules(filterGroup = null) {
        console.log('Populating rules with filter:', filterGroup);
        console.log('Available rules:', allRules);
        
        let filteredRules = allRules;
        if (filterGroup) {
            filteredRules = allRules.filter(rule => rule.group === filterGroup);
        }

        let options = '<option value="">Select Rule</option>';
        if (Array.isArray(filteredRules)) {
            filteredRules.forEach(rule => {
                const groupLabel = offenceGroup.querySelector(`option[value="${rule.group}"]`)?.textContent || '';
                options += `<option value="${rule.id}" data-group="${rule.group}" data-description="${rule.description}">${rule.rule_id} - ${rule.name}</option>`;
            });
        }
        offenceRule.innerHTML = options;
        console.log('Updated dropdown HTML:', offenceRule.innerHTML);

        // Update tooltips after populating options
        offenceRule.querySelectorAll('option').forEach(option => {
            if (option.dataset.description) {
                option.title = option.dataset.description;
            }
        });
    }

    function formatRule(rule) {
        if (!rule.id) return rule.text;

        const highlight = (text, term) => {
            if (!term) return text;
            return text.replace(new RegExp(escapeRegex(term), 'gi'), match => `<strong>${match}</strong>`);
        };
        
        const searchTerm = rule.element?.dataset?.searchTerm || '';
        const description = rule.rule?.description || '';
        const groupDisplay = rule.rule?.group_display || '';
        
        const $container = $(
            `<div class="rule-option p-2">
                <div class="rule-title fw-bold mb-1">${highlight(rule.text, searchTerm)}</div>
                <div class="rule-info small text-muted">
                    <div class="mb-1"><strong>Group:</strong> ${groupDisplay}</div>
                    <div class="text-wrap">${highlight(description, searchTerm)}</div>
                </div>
             </div>`
        );
        
        return $container;
    }

    function formatRuleSelection(rule) {
        if (!rule.id) return rule.text;
        return `${rule.rule?.rule_id} - ${rule.rule?.name}`;
    }

    // API Functions
    async function fetchAllRules() {
        try {
            console.log('Fetching rules...');
            const response = await fetch('/employees/api/offense-rules/');
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log('Raw API response:', data);
            
            allRules = Array.isArray(data) ? data : (data.results || []);
            console.log('Processed rules:', allRules);
            
            populateRules();
        } catch (error) {
            console.error('Error loading rules:', error);
            showAlert('Error loading rules. Please try again.', 'danger');
        }
    }

    async function updatePenalty(ruleId, year = new Date().getFullYear()) {
        try {
            const rule = allRules.find(r => r.id === parseInt(ruleId));
            if (!rule) return;
            
            currentRule = rule;
            
            // Get active offense count for the specified year
            const response = await fetch(`/employees/api/employee-offenses/${employeeId}/count/?rule=${ruleId}&year=${year}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            // Set the suggested penalty
            appliedPenalty.value = data.suggested_penalty;
            suggestedPenalty.textContent = appliedPenalty.options[appliedPenalty.selectedIndex].text;
            suggestedPenalty.dataset.value = data.suggested_penalty;
            penaltyNote.style.display = 'none';

            // Show description
            if (rule.description) {
                ruleDescriptionText.textContent = rule.description;
                ruleDescription.style.display = 'block';
            } else {
                ruleDescription.style.display = 'none';
            }

            // Update offense count and list
            offenseCount.textContent = data.count + 1;
            
            if (data.offenses && data.offenses.length > 0) {
                let offenseHtml = '<ul class="mb-2">';
                data.offenses.forEach((offense, index) => {
                    const date = new Date(offense.date).toLocaleDateString();
                    offenseHtml += `<li>Offense #${index + 1}: ${date} - ${offense.penalty}</li>`;
                });
                offenseHtml += '</ul>';
                
                previousOffensesList.innerHTML = offenseHtml;
                previousOffenses.style.display = 'block';
            } else {
                previousOffensesList.innerHTML = '<p class="mb-2">No previous offenses this year.</p>';
                previousOffenses.style.display = 'block';
            }
        } catch (error) {
            console.error('Error loading rule details:', error);
            showAlert('Error loading rule details. Please try again.', 'danger');
        }
    }





    function escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // Initialize and destroy Select2 when modal is shown/hidden
    $('#addOffenceModal').on('shown.bs.modal', function() {
        console.log('Modal shown, initializing select2...');
        
        // Initialize select2
        $('#offenseSearch').select2({
            width: '100%',
            placeholder: 'Search for offense rule...',
            minimumInputLength: 2,
            dropdownParent: $('#addOffenceModal'),
            ajax: {
                url: '/employees/api/offense-rules/',
                dataType: 'json',
                delay: 250,
                data: function(params) {
                    return {
                        search: params.term,
                        page: params.page || 1
                    };
                },
                processResults: function(data) {
                    return {
                        results: data.map(function(rule) {
                            return {
                                id: rule.id,
                                text: `${rule.rule_id} - ${rule.name}`,
                                rule: {
                                    ...rule,
                                    group_display: rule.group_display || rule.group
                                }
                            };
                        }),
                        pagination: {
                            more: false
                        }
                    };
                },
                cache: true
            },
            templateResult: formatRule,
            templateSelection: formatRuleSelection,
            escapeMarkup: function(markup) {
                return markup;
            }
        });
    }).on('hidden.bs.modal', function() {
        // Destroy select2 when modal is hidden
        try {
            $('#offenseSearch').select2('destroy');
        } catch (e) {
            console.log('No select2 instance to destroy');
        }
    });

        // Handle offense date change
        offenseDate.addEventListener('change', async function() {
            if (currentRule) {
                const year = new Date(this.value).getFullYear();
                offenseYear.textContent = year;
                await updatePenalty(currentRule.id, year);
            }
        });
    
        // Handle applied penalty change
        appliedPenalty.addEventListener('change', function() {
            const suggestedValue = suggestedPenalty.dataset.value;
            const monetaryPenaltySection = document.getElementById('monetaryPenaltySection');
            
            // Show/hide monetary penalty section based on penalty type
            if (this.value === 'MONETARY') {
                monetaryPenaltySection.style.display = 'block';
            } else {
                monetaryPenaltySection.style.display = 'none';
            }
    
            // Show warning if different from suggested penalty
            if (suggestedValue && this.value !== suggestedValue) {
                penaltyNote.style.display = 'block';
            } else {
                penaltyNote.style.display = 'none';
            }
        });

    // Handle offense status changes
    async function markOffenseStatus(offenseId, status) {
        try {
            const response = await fetch(`/employees/api/employee-offenses/${offenseId}/status/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ status })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Reload the page to show updated status
            location.reload();
        } catch (error) {
            console.error('Error updating offense status:', error);
            showAlert('Error updating offense status. Please try again.', 'danger');
        }
    }

    // Handle monetary penalty payments
    async function recordPayment(offenseId) {
        const amount = prompt('Enter payment amount (BHD):');
        if (!amount) return;

        try {
            const response = await fetch(`/employees/api/employee-offenses/${offenseId}/payment/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ amount: parseFloat(amount) })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Reload the page to show updated payment status
            location.reload();
        } catch (error) {
            console.error('Error recording payment:', error);
            showAlert('Error recording payment. Please try again.', 'danger');
        }
    }

    // Print offense
    async function printOffense(offenseId) {
        try {
            const response = await fetch(`/employees/api/employee-offenses/${offenseId}/print/`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // Create a blob from the PDF stream
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            
            // Open the PDF in a new window
            window.open(url);
        } catch (error) {
            console.error('Error generating offense print:', error);
            showAlert('Error generating offense print. Please try again.', 'danger');
        }
    }

    // Event Listeners
    $(offenseSearch).on('select2:select', async function(e) {
        const selectedRule = e.params.data.rule;
        if (selectedRule) {
            offenceGroup.value = selectedRule.group;
            await populateRules();
            offenceRule.value = selectedRule.id;
            await updatePenalty(selectedRule.id);
        }
    });

    offenceGroup.addEventListener('change', function() {
        const group = this.value;
        populateRules(group);
    });

    offenceRule.addEventListener('change', async function() {
        const ruleId = this.value;
        if (!ruleId) {
            ruleDescription.style.display = 'none';
            return;
        }

        const selectedOption = this.options[this.selectedIndex];
        const group = selectedOption.dataset.group;
        
        if (group && offenceGroup.value !== group) {
            offenceGroup.value = group;
        }

        await updatePenalty(ruleId);
    });

    // Handle offense date change
    offenseDate.addEventListener('change', async function() {
        if (currentRule) {
            const year = new Date(this.value).getFullYear();
            offenseYear.textContent = year;
            await updatePenalty(currentRule.id, year);
        }
    });

    // Handle applied penalty change
    appliedPenalty.addEventListener('change', function() {
        const suggestedValue = suggestedPenalty.dataset.value;
        const monetaryPenaltySection = document.getElementById('monetaryPenaltySection');
        
        // Show/hide monetary penalty section based on penalty type
        if (this.value === 'MONETARY') {
            monetaryPenaltySection.style.display = 'block';
        } else {
            monetaryPenaltySection.style.display = 'none';
        }

        // Show warning if different from suggested penalty
        if (suggestedValue && this.value !== suggestedValue) {
            penaltyNote.style.display = 'block';
        } else {
            penaltyNote.style.display = 'none';
        }
    });

    // Handle save offense
    document.getElementById('saveOffenceBtn').addEventListener('click', async function() {
        try {
            const formData = new FormData(addOffenceForm);
            
            // Add employee ID to form data
            formData.append('employee', employeeId);
            
            // Get the rule ID from the select element
            const ruleId = offenceRule.value;
            if (!ruleId) {
                showAlert('Please select an offense rule.', 'danger');
                return;
            }
            
            // Remove the old 'rule' field and add the correct 'offense_rule' field
            formData.delete('rule');
            formData.append('offense_rule', ruleId);
            
            // If it's a monetary penalty, add the monetary fields
            if (appliedPenalty.value === 'MONETARY') {
                const monetaryAmount = document.getElementById('monetaryAmount').value;
                const monthlyDeduction = document.getElementById('monthlyDeduction').value;
                
                if (!monetaryAmount || monetaryAmount <= 0) {
                    showAlert('Please enter a valid monetary penalty amount.', 'danger');
                    return;
                }
                
                if (!monthlyDeduction || monthlyDeduction <= 0) {
                    showAlert('Please enter a valid monthly deduction amount.', 'danger');
                    return;
                }
                
                formData.append('monetary_amount', monetaryAmount);
                formData.append('monthly_deduction', monthlyDeduction);
            }

            const response = await fetch('/employees/api/employee-offenses/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || error.detail || 'Failed to save offense');
            }
            
            const offense = await response.json();
            
            // Clear form and close modal
            addOffenceForm.reset();
            monetaryPenaltySection.style.display = 'none';
            addOffenceModal.hide();
            
            // Show success message and reload page
            showAlert('Offense added successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } catch (error) {
            console.error('Error saving offense:', error);
            showAlert(error.message || 'Error saving offense. Please try again.', 'danger');
        }
    });

    // Handle view offense
    document.addEventListener('click', function(e) {
        const viewBtn = e.target.closest('.view-offence');
        if (viewBtn) {
            e.preventDefault();
            viewOffence(viewBtn.dataset.offenceId);
        }
    });

    // Handle add document
    document.addEventListener('click', function(e) {
        const addDocBtn = e.target.closest('.add-document');
        if (addDocBtn) {
            e.preventDefault();
            document.getElementById('documentOffenseId').value = addDocBtn.dataset.offenceId;
            addDocumentModal.show();
        }
    });

    // Handle save document
    document.getElementById('saveDocumentBtn').addEventListener('click', async function() {
        if (!addDocumentForm.checkValidity()) {
            addDocumentForm.reportValidity();
            return;
        }

        const formData = new FormData(addDocumentForm);
        
        try {
            const response = await fetch('/employees/api/offense-documents/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            });

            if (!response.ok) throw new Error('Failed to save document');
            
            addDocumentModal.hide();
            addDocumentForm.reset();
            showAlert('Document added successfully!', 'success');
            
            // Refresh offense details if viewing
            const offenseId = formData.get('offense_id');
            if (viewOffenceModal._isShown) {
                viewOffence(offenseId);
            }
        } catch (error) {
            console.error('Error saving document:', error);
            showAlert('Error saving document. Please try again.', 'danger');
        }
    });

    // Initialize
    fetchAllRules();
});

// Utility Functions
function addOffenceToTable(offense) {
    const tbody = document.querySelector('#offencesTable tbody');
    const tr = document.createElement('tr');
    tr.dataset.offenceId = offense.id;
    
    if (!offense.is_active) {
        tr.classList.add('table-secondary');
    }
    
    const offenseDate = new Date(offense.offense_date);
    
    tr.innerHTML = `
        <td>${offense.rule.rule_id}</td>
        <td>${offenseDate.toLocaleDateString()}</td>
        <td>${offenseDate.getFullYear()}</td>
        <td>${offense.rule.group_display}</td>
        <td>${offense.rule.name}</td>
        <td>${offense.offense_count}</td>
        <td>${offense.original_penalty_display}</td>
        <td>${offense.applied_penalty_display}</td>
        <td>
            ${offense.is_active ? 
                `<span class="badge ${offense.is_acknowledged ? 'bg-success' : 'bg-warning'}">
                    ${offense.is_acknowledged ? 'Acknowledged' : 'Pending'}
                </span>` :
                '<span class="badge bg-secondary">Inactive</span>'
            }
        </td>
        <td>
            <button type="button" class="btn btn-sm btn-info view-offence" data-offence-id="${offense.id}" title="View Details">
                <i class="fas fa-eye"></i>
            </button>
            ${offense.is_active ? 
                `<button type="button" class="btn btn-sm btn-primary add-document" data-offence-id="${offense.id}" title="Add Document">
                    <i class="fas fa-file-upload"></i>
                </button>` : ''
            }
        </td>
    `;
    
    tbody.insertBefore(tr, tbody.firstChild);
}

async function viewOffence(offenseId) {
    try {
        // Get offense details
        const response = await fetch(`/employees/api/employee-offenses/${offenseId}/`);
        const offense = await response.json();
        
        // Update offense details
        document.getElementById('viewRuleId').textContent = offense.rule.rule_id;
        document.getElementById('viewRuleName').textContent = offense.rule.name;
        document.getElementById('viewGroup').textContent = offense.rule.group_display;
        document.getElementById('viewDescription').textContent = offense.rule.description;
        document.getElementById('viewDate').textContent = new Date(offense.offense_date).toLocaleDateString();
        document.getElementById('viewOriginalPenalty').textContent = offense.original_penalty_display;
        document.getElementById('viewAppliedPenalty').textContent = offense.applied_penalty_display;
        document.getElementById('viewStatus').innerHTML = offense.is_active ? 
            `<span class="badge ${offense.is_acknowledged ? 'bg-success' : 'bg-warning'}">
                ${offense.is_acknowledged ? 'Acknowledged' : 'Pending'}
            </span>` :
            '<span class="badge bg-secondary">Inactive</span>';

        // Get offense count and history
        const year = new Date(offense.offense_date).getFullYear();
        const countResponse = await fetch(`/employees/api/employee-offenses/${offense.employee}/count/?rule=${offense.rule.id}&year=${year}`);
        if (!countResponse.ok) {
            throw new Error(`HTTP error! status: ${countResponse.status}`);
        }
        const countData = await countResponse.json();

        // Show previous offenses if any exist
        const viewPreviousOffenses = document.getElementById('viewPreviousOffenses');
        const viewPreviousOffensesList = document.getElementById('viewPreviousOffensesList');
        
        if (countData.offenses && countData.offenses.length > 0) {
            let offenseHtml = `<p class="mb-2">This is offense #${countData.count} for this rule in ${year}.</p>`;
            offenseHtml += '<ul class="mb-0">';
            countData.offenses.forEach((o, index) => {
                const date = new Date(o.date).toLocaleDateString();
                const isCurrent = o.date === offense.offense_date;
                offenseHtml += `<li${isCurrent ? ' class="fw-bold"' : ''}>${date} - ${o.penalty}${isCurrent ? ' (Current)' : ''}</li>`;
            });
            offenseHtml += '</ul>';
            
            viewPreviousOffensesList.innerHTML = offenseHtml;
            viewPreviousOffenses.style.display = 'block';
        } else {
            viewPreviousOffenses.style.display = 'none';
        }

        // Update documents list
        const documentsList = document.getElementById('viewDocumentsList');
        if (offense.documents && offense.documents.length > 0) {
            let docsHtml = '<ul class="list-unstyled mb-0">';
            offense.documents.forEach(doc => {
                docsHtml += `
                    <li class="mb-2">
                        <i class="fas fa-file me-2"></i>
                        <a href="${doc.file_url}" target="_blank">${doc.name || 'Document'}</a>
                        <small class="text-muted">(${doc.document_type_display})</small>
                    </li>`;
            });
            docsHtml += '</ul>';
            documentsList.innerHTML = docsHtml;
        } else {
            documentsList.innerHTML = '<p class="text-muted mb-0">No documents attached</p>';
        }

        // Show the modal
        const viewOffenceModal = new bootstrap.Modal('#viewOffenceModal');
        viewOffenceModal.show();
    } catch (error) {
        console.error('Error loading offense details:', error);
        showAlert('Error loading offense details. Please try again.', 'danger');
    }
}

function showAlert(message, type = 'info') {
    const alertsContainer = document.getElementById('alerts-container');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    alertsContainer.appendChild(alert);
    setTimeout(() => alert.remove(), 5000);
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
