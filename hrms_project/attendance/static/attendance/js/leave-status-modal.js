// Leave Status Modal Handler
class LeaveStatusModal {
    constructor() {
        console.log('LeaveStatusModal constructor starting...');
        
        // Check for required dependencies
        console.log('Checking dependencies:', {
            bootstrap: typeof bootstrap !== 'undefined',
            jQuery: typeof $ !== 'undefined'
        });
        
        this.modalElement = document.getElementById('statusChangeModal');
        console.log('Modal element found:', !!this.modalElement);
        
        this.statusSelect = document.getElementById('newStatus');
        this.remarksInput = document.getElementById('statusRemarks');
        this.confirmBtn = document.getElementById('confirmStatusChange');
        
        console.log('Required elements found:', {
            statusSelect: !!this.statusSelect,
            remarksInput: !!this.remarksInput,
            confirmBtn: !!this.confirmBtn
        });
        
        this.modal = null;
        
        if (this.modalElement && typeof bootstrap !== 'undefined') {
            console.log('Initializing Bootstrap modal...');
            try {
                this.modal = new bootstrap.Modal(this.modalElement);
                console.log('Bootstrap modal created successfully');
                this.initialize();
            } catch (error) {
                console.error('Failed to create Bootstrap modal:', error);
            }
        } else {
            console.error('Cannot initialize modal:', {
                modalElement: !!this.modalElement,
                bootstrap: typeof bootstrap !== 'undefined'
            });
        }
    }

    initialize() {
        console.log('Starting modal initialization...');
        if (!this.statusSelect || !this.remarksInput || !this.confirmBtn) {
            console.error('Missing required elements:', {
                statusSelect: !!this.statusSelect,
                remarksInput: !!this.remarksInput,
                confirmBtn: !!this.confirmBtn
            });
            return;
        }

        this.bindEvents();
        console.log('Modal initialization complete');
    }

    bindEvents() {
        console.log('Binding modal events...');
        const buttons = document.querySelectorAll('.change-status-btn');
        console.log(`Found ${buttons.length} status change buttons`);

        buttons.forEach((button, index) => {
            console.log(`Setting up button ${index}:`, {
                status: button.dataset.status,
                id: button.dataset.id
            });
            
            button.addEventListener('click', (e) => {
                console.log(`Button ${index} clicked`);
                e.preventDefault();
                this.handleButtonClick(e);
            });
        });

        this.confirmBtn.addEventListener('click', () => {
            console.log('Confirm button clicked');
            this.handleStatusChange();
        });
        
        console.log('Event binding complete');
    }

    handleButtonClick(e) {
        const button = e.target.closest('.change-status-btn');
        if (!button) {
            console.error('Could not find button element');
            return;
        }

        const currentStatus = button.dataset.status;
        const leaveId = button.dataset.id;
        console.log('Button clicked:', { currentStatus, leaveId });

        if (!currentStatus || !leaveId) {
            console.error('Missing required data attributes');
            return;
        }

        this.currentLeaveId = leaveId;
        this.show(currentStatus, leaveId);
    }

    show(currentStatus, leaveId) {
        console.log('Showing modal for status:', currentStatus, 'leaveId:', leaveId);
        
        if (!this.modal) {
            console.error('Modal not initialized');
            return;
        }

        // Update status options
        const statusToAction = {
            'pending': '',
            'approved': 'approve',
            'rejected': 'reject',
            'cancelled': 'cancel'
        };

        Array.from(this.statusSelect.options).forEach(option => {
            option.style.display = option.value === statusToAction[currentStatus] ? 'none' : '';
        });

        // Clear previous remarks
        this.remarksInput.value = '';

        // Show modal
        this.modal.show();
    }

    async handleStatusChange() {
        const newStatus = this.statusSelect.value;
        const remarks = this.remarksInput.value;

        console.log('Handling status change:', {
            leaveId: this.currentLeaveId,
            status: newStatus,
            remarks: remarks
        });

        try {
            const response = await fetch(`/attendance/api/leaves/${this.currentLeaveId}/${newStatus}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({ remarks })
            });

            console.log('Response status:', response.status);
            const data = await response.json();
            console.log('Response data:', data);

            if (data.error) {
                throw new Error(data.error);
            }

            // Hide modal and reload page on success
            this.modal.hide();
            window.location.reload();

        } catch (error) {
            console.error('API Error:', error);
            alert('Error updating leave status: ' + error.message);
        }
    }

    getCookie(name) {
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
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Modal handler script loaded, waiting for dependencies...');
    
    function checkDependencies() {
        console.log('Checking dependencies:', {
            bootstrap: typeof bootstrap !== 'undefined',
            jQuery: typeof $ !== 'undefined'
        });
        
        if (typeof bootstrap === 'undefined') {
            console.log('Bootstrap not yet loaded, retrying...');
            setTimeout(checkDependencies, 100);
            return;
        }
        
        console.log('Dependencies loaded, creating modal handler');
        window.leaveStatusModal = new LeaveStatusModal();
    }
    
    checkDependencies();
}); 