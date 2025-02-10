# HRMS Project

A comprehensive Human Resource Management System with advanced attendance tracking, shift management, and Ramadan period handling.

## Features

### Core Features
- Employee Management
- Leave Management
- Attendance Tracking
- Holiday Management
- Reporting System

### Shift Management
- Multiple shift types support (Regular, Night, Split)
- Flexible shift assignments
- Automatic shift validation
- Grace period handling
- Break time management
- Department-wise shift allocation
- Shift statistics and reports

### Ramadan Period Management
- Automatic working hours adjustment
- Yearly Ramadan period configuration
- Smart cache management
- Notification system for schedule changes
- Department-wide adjustments

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hrms-project.git
cd hrms-project
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Initialize default data:
```bash
python manage.py init_shift_types
python manage.py init_ramadan_periods
python manage.py init_leave_types
```

## Configuration

### Shift Management
Configure shift types in settings:
```python
SHIFT_SETTINGS = {
    'DEFAULT_GRACE_PERIOD': 15,  # minutes
    'MAX_BREAK_DURATION': 180,   # minutes
    'MIN_SHIFT_DURATION': 240,   # minutes
    'AUTO_ADJUST_RAMADAN': True
}
```

### Ramadan Settings
Configure Ramadan adjustments:
```python
RAMADAN_SETTINGS = {
    'HOURS_REDUCTION': 2,        # hours to reduce
    'CACHE_TIMEOUT': 86400,      # 24 hours
    'NOTIFICATION_DAYS': 7       # days before to notify
}
```

## Usage

### Managing Shifts

1. Create Shifts:
```python
from attendance.models import Shift
shift = Shift.objects.create(
    name='Morning Shift',
    shift_type='REGULAR',
    start_time='09:00',
    end_time='17:00',
    break_duration=60
)
```

2. Assign Shifts:
```python
from attendance.services import ShiftService
ShiftService.assign_shift(
    employee=employee,
    shift=shift,
    start_date=date.today()
)
```

### Managing Ramadan Periods

1. Create Ramadan Period:
```python
from attendance.models import RamadanPeriod
period = RamadanPeriod.objects.create(
    year=2025,
    start_date=date(2025, 3, 1),
    end_date=date(2025, 3, 30)
)
```

2. Check Active Period:
```python
from attendance.services import RamadanService
active_period = RamadanService.get_active_period(date.today())
```

## Maintenance

### Data Cleanup
Run periodic cleanup:
```bash
# Clean up old data (90 days)
python manage.py cleanup_shifts

# With archiving
python manage.py cleanup_shifts --archive

# Dry run
python manage.py cleanup_shifts --dry-run
```

### Cache Management
Clear shift-related caches:
```python
from attendance.cache import ShiftCache, RamadanCache
ShiftCache.clear_employee_shift(employee_id)
RamadanCache.clear_all_periods()
```

## Testing

Run specific test modules:
```bash
# Run shift tests
python manage.py test attendance.tests.test_shifts

# Run Ramadan tests
python manage.py test attendance.tests.test_ramadan

# Run cleanup tests
python manage.py test attendance.tests.test_cleanup_shifts
```

## Celery Tasks

Start Celery worker:
```bash
celery -A hrms_project worker -l info
```

Start beat scheduler:
```bash
celery -A hrms_project beat -l info
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
