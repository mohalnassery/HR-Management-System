# HR Management System

A comprehensive HR Management System built with Django for CityGlass.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL
- pip (Python package manager)

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/HR-Management-System.git
cd HR-Management-System
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup

1. Install PostgreSQL if not already installed
2. Create a new PostgreSQL database:
```sql
CREATE DATABASE hrms_db;
CREATE USER hradmin WITH PASSWORD 'your_postgres_password';
ALTER ROLE hradmin SET client_encoding TO 'utf8';
ALTER ROLE hradmin SET default_transaction_isolation TO 'read committed';
ALTER ROLE hradmin SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE hrms_db TO hradmin;
```

### 5. Environment Configuration

Create a `.env` file in the project directory with the following settings:
```
DB_NAME=hrms_db
DB_USER=HRAdmin
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
```

### 6. Django Setup

1. Apply migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

2. Create a superuser:
```bash
python manage.py createsuperuser
```

3. Run the development server:
```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Accessing the Admin Interface

1. Go to `http://127.0.0.1:8000/admin`
2. Log in with your superuser credentials

## Features

- Employee Management
- Attendance Tracking
- Leave Management
- Performance Reviews
- Payroll Management

## Support

For any issues or questions, please open an issue in the repository.
