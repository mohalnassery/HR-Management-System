class RamadanPeriodManager {
    constructor() {
        this.deleteId = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            // Set current year as default
            const currentYear = new Date().getFullYear();
            const yearInput = document.getElementById('year');
            if (yearInput) {
                yearInput.value = currentYear;
            }
            
            // Add date validation listeners
            ['start_date', 'end_date'].forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    element.addEventListener('change', () => this.validatePeriod('add'));
                }
            });

            ['edit_start_date', 'edit_end_date'].forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    element.addEventListener('change', () => this.validatePeriod('edit'));
                }
            });
        });
    }

    validatePeriod(mode) {
        const prefix = mode === 'edit' ? 'edit_' : '';
        const startDate = document.getElementById(`${prefix}start_date`).value;
        const endDate = document.getElementById(`${prefix}end_date`).value;
        const validation = document.getElementById(`${prefix}periodValidation`);
        const message = document.getElementById(`${prefix}validationMessage`);
        
        if (startDate && endDate) {
            const start = new Date(startDate);
            const end = new Date(endDate);
            const days = Math.floor((end - start) / (1000 * 60 * 60 * 24)) + 1;
            
            if (days < 28 || days > 31) {
                validation.classList.remove('d-none', 'alert-info');
                validation.classList.add('alert-warning');
                message.textContent = `Duration (${days} days) seems unusual for Ramadan`;
            } else {
                validation.classList.remove('d-none', 'alert-warning');
                validation.classList.add('alert-info');
                message.textContent = `Duration: ${days} days`;
            }
        }
    }

    async savePeriod() {
        const form = document.getElementById('addPeriodForm');
        const data = {
            year: parseInt(form.querySelector('#year').value),
            start_date: form.querySelector('#start_date').value,
            end_date: form.querySelector('#end_date').value
        };
        
        try {
            const response = await fetch('/attendance/ramadan_period_add/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            if (response.ok) {
                location.reload();
            } else {
                throw new Error(result.error || 'Error adding Ramadan period');
            }
        } catch (error) {
            alert(error.message);
        }
    }

    async editPeriod(id) {
        try {
            const response = await fetch(`/attendance/ramadan_period_detail/${id}/`);
            const data = await response.json();
            
            // Populate form
            document.getElementById('edit_period_id').value = id;
            document.getElementById('edit_year').value = data.year;
            document.getElementById('edit_start_date').value = data.start_date;
            document.getElementById('edit_end_date').value = data.end_date;
            document.getElementById('edit_is_active').checked = data.is_active;
            
            this.validatePeriod('edit');
            
            // Show modal
            new bootstrap.Modal(document.getElementById('editPeriodModal')).show();
        } catch (error) {
            alert('Error loading period details');
        }
    }

    async updatePeriod() {
        const id = document.getElementById('edit_period_id').value;
        const data = {
            year: parseInt(document.getElementById('edit_year').value),
            start_date: document.getElementById('edit_start_date').value,
            end_date: document.getElementById('edit_end_date').value,
            is_active: document.getElementById('edit_is_active').checked
        };
        
        try {
            const response = await fetch(`/attendance/ramadan_period_detail/${id}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                location.reload();
            } else {
                const result = await response.json();
                throw new Error(result.error || 'Error updating Ramadan period');
            }
        } catch (error) {
            alert(error.message);
        }
    }

    confirmDelete(id) {
        this.deleteId = id;
        new bootstrap.Modal(document.getElementById('deleteModal')).show();
    }

    async deletePeriod() {
        if (!this.deleteId) return;
        
        try {
            const response = await fetch(`/attendance/ramadan_period_detail/${this.deleteId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });
            
            if (response.ok) {
                location.reload();
            } else {
                throw new Error('Error deleting Ramadan period');
            }
        } catch (error) {
            alert(error.message);
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

// Initialize the manager
const ramadanManager = new RamadanPeriodManager();

// Export for global access
window.ramadanManager = ramadanManager;
