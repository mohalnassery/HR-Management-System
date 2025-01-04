python hrms_project/manage.py runserver

# HR Management System (HRMS)

A comprehensive HR Management System built with Django, designed to handle various aspects of human resource management including employee management, attendance tracking, performance evaluation, and payroll processing.

## Features

- Employee Management
- Attendance & Leave Management
- Performance Management
- Payroll Management
- API Integration
- And more...

## Project Structure

```
hrms_project/
  ├── hrms_project/     # Project settings
  ├── core/             # Core functionality
  ├── employees/        # Employee management
  ├── attendance/       # Attendance tracking
  ├── performance/      # Performance management
  ├── payroll/         # Payroll processing
  └── api/             # API endpoints
```

## Setup Instructions

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   - Create a `.env` file in the project root
   - Add necessary environment variables (see `.env.example`)

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Technology Stack

- Django 5.1.4
- Django REST Framework
- PostgreSQL
- Celery
- Redis
- Bootstrap 5
- And more...

## Contributing

Please read our contributing guidelines before submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
