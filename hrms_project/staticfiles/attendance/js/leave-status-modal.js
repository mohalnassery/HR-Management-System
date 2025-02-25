// Leave Status Modal Handler
class LeaveStatusModal {
    constructor() {
        this.modalElement = document.getElementById('statusChangeModal');
        this.statusSelect = document.getElementById('newStatus');
        this.remarksInput = document.getElementById('statusRemarks');
        this.confirmBtn = document.getElementById('confirmStatusChange');
        this.modal = null;
        
        this.initialize();
    }

    initialize() {
        console.log('Initializing LeaveStatusModal');
        if (!this.modalElement || !this.statusSelect || !this.remarksInput || !this.confirmBtn) {
            console.error('Required modal elements not found');
            return;
        }

        try {
            this.modal = new bootstrap.Modal(this.modalElement);
            console.log('Modal initialized successfully');
        } catch (error) {
            console.error('Error initializing modal:', error);
            return;
        }

        // Bind event listeners
        this.bindEvents();
    }

    bindEvents() {
        // Bind click events to all change status buttons
        document.querySelectorAll('.change-status-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const currentStatus = e.target.closest('.change-status-btn').dataset.status;
                const leaveId = e.target.closest('.change-status-btn').dataset.id;
                this.show(currentStatus, leaveId);
            });
        });

        // Bind confirmation button
        this.confirmBtn.addEventListener('click', () => this.handleStatusChange());
    }

    show(currentStatus, leaveId) {
        console.log('Showing modal for status:', currentStatus, 'leaveId:', leaveId);
        
        // Store leave ID for use in handleStatusChange
        this.currentLeaveId = leaveId;
        
        // Map current status to action
        const statusToAction = {
            'pending': '',
            'approved': 'approve',
            'rejected': 'reject',
            'cancelled': 'cancel'
        };

        // Remove current status from options
        Array.from(this.statusSelect.options).forEach(option => {
            const shouldHide = option.value === statusToAction[currentStatus];
            option.style.display = shouldHide ? 'none' : '';
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
    console.log('Initializing leave status modal handler');
    window.leaveStatusModal = new LeaveStatusModal();
}); 