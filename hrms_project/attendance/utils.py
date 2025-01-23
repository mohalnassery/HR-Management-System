import pandas as pd
from datetime import datetime, time, timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import F
from .models import Attendance
from employees.models import Employee

def process_attendance_excel(file_path):
    """
    Process attendance Excel file from the machine
    Expected columns: Date And Time, Personnel ID, Device Name, Event Point, 
                     Verify Type, Event Description, Remarks
    Returns: records_created, duplicates, total_records, new_employees, unique_dates
    """
    try:
        # Determine the engine based on file extension
        file_extension = str(file_path).lower()
        engine = 'xlrd' if file_extension.endswith('.xls') else 'openpyxl'
        
        # Read Excel file
        df = pd.read_excel(file_path, engine=engine)
        
        if df.empty:
            return 0, 0, 0, [], set()
            
        # Standardize column names
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        
        # Verify required columns
        required_columns = ['date_and_time', 'personnel_id']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise Exception(f"Missing required columns: {', '.join(missing_columns)}")
        
        records_created = 0
        duplicates = 0
        new_employees = []
        unique_dates = set()
        
        # Get existing employee numbers
        existing_employee_numbers = set(Employee.objects.values_list('employee_number', flat=True))
        
        # Group by employee and date to consolidate records
        df['date'] = pd.to_datetime(df['date_and_time']).dt.date
        for (personnel_id, date), group in df.groupby(['personnel_id', 'date']):
            try:
                # Convert timestamps
                timestamps = pd.to_datetime(group['date_and_time'])
                unique_dates.add(date)
                
                # Try to get employee or create placeholder
                try:
                    employee = Employee.objects.get(employee_number=personnel_id)
                except Employee.DoesNotExist:
                    if personnel_id not in existing_employee_numbers:
                        employee = Employee.objects.create(
                            employee_number=personnel_id,
                            first_name=f"Employee {personnel_id}",
                            last_name='',
                            email=f"employee{personnel_id}@placeholder.com"
                        )
                        new_employees.append({
                            'id': employee.id,
                            'employee_number': employee.employee_number,
                            'name': employee.get_full_name().strip()
                        })
                        existing_employee_numbers.add(personnel_id)
                    else:
                        employee = Employee.objects.get(employee_number=personnel_id)
                
                # Get first and last timestamps
                first_record = group.iloc[0]
                last_record = group.iloc[-1]
                first_time = pd.to_datetime(first_record['date_and_time'])
                last_time = pd.to_datetime(last_record['date_and_time'])
                
                # Create or update attendance record
                attendance, created = Attendance.objects.get_or_create(
                    employee=employee,
                    date=date,
                    defaults={
                        'timestamp': first_time,
                        'first_in_time': first_time.time(),
                        'last_out_time': last_time.time(),
                        'device_name': first_record.get('device_name', ''),
                        'event_point': first_record.get('event_point', ''),
                        'verify_type': first_record.get('verify_type', ''),
                        'event_description': first_record.get('event_description', ''),
                        'source': 'machine',
                        'original_first_in': first_time.time(),
                        'original_last_out': last_time.time()
                    }
                )
                
                if not created:
                    duplicates += 1
                else:
                    records_created += 1
                    
            except Exception as e:
                continue
        
        total_records = Attendance.objects.count()
        
        return records_created, duplicates, total_records, new_employees, unique_dates
        
    except Exception as e:
        raise Exception(f"Error processing Excel file: {str(e)}")

def validate_attendance_edit(attendance, new_in_time, new_out_time, reason, editor):
    """
    Validate attendance edit times and track changes
    Returns: (is_valid, error_message)
    """
    try:
        # Convert string times to time objects if necessary
        if isinstance(new_in_time, str):
            new_in_time = datetime.strptime(new_in_time, '%H:%M').time()
        if isinstance(new_out_time, str):
            new_out_time = datetime.strptime(new_out_time, '%H:%M').time()
        
        # Basic validation
        if new_in_time > new_out_time:
            return False, "First in time cannot be after last out time"
        
        # Check if times are within 24 hours
        time_diff = datetime.combine(datetime.today(), new_out_time) - \
                   datetime.combine(datetime.today(), new_in_time)
        
        if time_diff > timedelta(hours=24):
            return False, "Time difference cannot be more than 24 hours"
            
        # Store original times if this is first edit
        if not attendance.original_first_in:
            attendance.original_first_in = attendance.first_in_time
        if not attendance.original_last_out:
            attendance.original_last_out = attendance.last_out_time
            
        # Update times and edit information
        attendance.first_in_time = new_in_time
        attendance.last_out_time = new_out_time
        attendance.edit_timestamp = timezone.now()
        attendance.edit_reason = reason
        attendance.edited_by = editor
        attendance.save()
        
        return True, None
        
    except ValueError as e:
        return False, f"Invalid time format or values: {str(e)}"
    except Exception as e:
        return False, str(e)

def get_attendance_summary(employee, start_date, end_date):
    """
    Get attendance summary for an employee within a date range
    """
    records = Attendance.objects.filter(
        employee=employee,
        date__range=(start_date, end_date),
        is_active=True
    ).order_by('date')
    
    summary = {
        'total_days': (end_date - start_date).days + 1,
        'present_days': records.count(),
        'absent_days': 0,  # Will be calculated as total_days - present_days
        'late_days': records.filter(
            first_in_time__gt=F('shift__start_time')
        ).count(),
        'edited_days': records.exclude(edit_timestamp=None).count(),
        'attendance_details': []
    }
    
    for record in records:
        # Calculate total hours for the day
        if record.first_in_time and record.last_out_time:
            in_datetime = datetime.combine(record.date, record.first_in_time)
            out_datetime = datetime.combine(record.date, record.last_out_time)
            if out_datetime < in_datetime:  # Handle overnight shift
                out_datetime += timedelta(days=1)
            total_hours = (out_datetime - in_datetime).total_seconds() / 3600
        else:
            total_hours = 0

        summary['attendance_details'].append({
            'date': record.date,
            'first_in': record.first_in_time,
            'last_out': record.last_out_time,
            'original_in': record.original_first_in,
            'original_out': record.original_last_out,
            'is_late': record.first_in_time > (record.shift.start_time if record.shift else time(8, 0)),
            'source': record.source,
            'edited': record.edit_timestamp is not None,
            'edited_by': record.edited_by.get_full_name() if record.edited_by else None,
            'edit_reason': record.edit_reason,
            'total_hours': round(total_hours, 2)
        })
    
    summary['absent_days'] = summary['total_days'] - summary['present_days']
    
    return summary
