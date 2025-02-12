class RamadanPeriodManager {
    constructor() {
        this.addModal = new bootstrap.Modal(document.getElementById('addPeriodModal'));
        this.editModal = new bootstrap.Modal(document.getElementById('editPeriodModal'));
        this.initializeEventListeners();
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

    async savePeriod() {
        const form = document.getElementById('addPeriodForm');
        const formData = new FormData(form);
        const data = {
            year: parseInt(formData.get('year')),
            start_date: formData.get('start_date'),
            end_date: formData.get('end_date'),
            is_active: formData.get('is_active') === 'on'
        };

        try {
            const response = await fetch('/attendance/ramadan_period/add/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            if (response.ok) {
                this.addModal.hide();
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
            const response = await fetch(`/attendance/ramadan_period/${id}/`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });

            const period = await response.json();
            if (response.ok) {
                const form = document.getElementById('editPeriodForm');
                form.querySelector('[name="id"]').value = period.id;
                form.querySelector('[name="year"]').value = period.year;
                form.querySelector('[name="start_date"]').value = period.start_date;
                form.querySelector('[name="end_date"]').value = period.end_date;
                form.querySelector('[name="is_active"]').checked = period.is_active;
                this.editModal.show();
            } else {
                throw new Error(period.error || 'Error fetching Ramadan period');
            }
        } catch (error) {
            alert(error.message);
        }
    }

    async updatePeriod() {
        const form = document.getElementById('editPeriodForm');
        const formData = new FormData(form);
        const id = formData.get('id');
        const data = {
            year: parseInt(formData.get('year')),
            start_date: formData.get('start_date'),
            end_date: formData.get('end_date'),
            is_active: formData.get('is_active') === 'on'
        };

        try {
            const response = await fetch(`/attendance/ramadan_period/${id}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                this.editModal.hide();
                location.reload();
            } else {
                const result = await response.json();
                throw new Error(result.error || 'Error updating Ramadan period');
            }
        } catch (error) {
            alert(error.message);
        }
    }

    async deletePeriod(id) {
        if (!confirm('Are you sure you want to delete this Ramadan period?')) {
            return;
        }

        try {
            const response = await fetch(`/attendance/ramadan_period/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });

            if (response.ok) {
                location.reload();
            } else {
                const result = await response.json();
                throw new Error(result.error || 'Error deleting Ramadan period');
            }
        } catch (error) {
            alert(error.message);
        }
    }

    validatePeriod(form) {
        const year = parseInt(form.querySelector('[name="year"]').value);
        const startDate = new Date(form.querySelector('[name="start_date"]').value);
        const endDate = new Date(form.querySelector('[name="end_date"]').value);

        if (startDate > endDate) {
            alert('End date cannot be before start date');
            return false;
        }

        if (startDate.getFullYear() !== year || endDate.getFullYear() !== year) {
            alert('Start and end dates must be within the specified year');
            return false;
        }

        return true;
    }

    initializeEventListeners() {
        // Add form submit event
        const addForm = document.getElementById('addPeriodForm');
        const addSaveBtn = document.querySelector('#addPeriodModal .btn-primary');
        addSaveBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.validatePeriod(addForm)) {
                this.savePeriod();
            }
        });

        // Edit form submit event
        const editForm = document.getElementById('editPeriodForm');
        const editSaveBtn = document.querySelector('#editPeriodModal .btn-primary');
        editSaveBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.validatePeriod(editForm)) {
                this.updatePeriod();
            }
        });

        // Year field change handlers
        [addForm, editForm].forEach(form => {
            const yearInput = form.querySelector('[name="year"]');
            const startDateInput = form.querySelector('[name="start_date"]');
            const endDateInput = form.querySelector('[name="end_date"]');

            yearInput.addEventListener('change', () => {
                const year = yearInput.value;
                startDateInput.min = `${year}-01-01`;
                startDateInput.max = `${year}-12-31`;
                endDateInput.min = `${year}-01-01`;
                endDateInput.max = `${year}-12-31`;
            });
        });
    }
}
