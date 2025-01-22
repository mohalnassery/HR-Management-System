import pandas as pd
from datetime import datetime, time, timedelta
from django.utils import timezone
from django.db import transaction
from .models import AttendanceRecord, AttendanceLog
from employees.models import Employee

def process_attendance_excel(file_path):
    """
    Process attendance Excel file from the machine
    Expected columns: Date And Time, Personnel ID, Device Name, Event Point, 
                     Verify Type, Event Description, Remarks
    """
    try:
        # Determine the engine based on file extension
        file_extension = str(file_path).lower()
        engine = 'xlrd' if file_extension.endswith('.xls') else 'openpyxl'
        
        # Read Excel file
        df = pd.read_excel(file_path, engine=engine)
        
        if df.empty:
            return 0, 0
            
        # Standardize column names
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        
        # Verify required columns
        required_columns = ['date_and_time', 'personnel_id']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise Exception(f"Missing required columns: {', '.join(missing_columns)}")
        
        records_to_create = []
        duplicates = 0
        
        # Get existing timestamps for each employee to check duplicates
        existing_records = {
            (str(r.employee_id), r.timestamp.strftime('%Y-%m-%d %H:%M:%S')): True 
            for r in AttendanceRecord.objects.all()
        }
        
        for _, row in df.iterrows():
            try:
                # Convert date_and_time to datetime
                timestamp = pd.to_datetime(row['date_and_time'])
                
                # Try to get employee or create placeholder
                try:
                    employee = Employee.objects.get(employee_number=row['personnel_id'])
                except Employee.DoesNotExist:
                    employee = Employee.objects.create(
                        employee_number=row['personnel_id'],
                        first_name=row.get('first_name', f"Employee {row['personnel_id']}"),
                        last_name=row.get('last_name', ''),
                        email=f"employee{row['personnel_id']}@placeholder.com"
                    )
                
                # Check for duplicates
                record_key = (str(employee.id), timestamp.strftime('%Y-%m-%d %H:%M:%S'))
                if record_key in existing_records:
                    duplicates += 1
                    continue
                
                # Create attendance record
                record = AttendanceRecord(
                    employee=employee,
                    timestamp=timestamp,
                    device_name=row.get('device_name', ''),
                    event_point=row.get('event_point', ''),
                    verify_type=row.get('verify_type', ''),
                    event_description=row.get('event_description', ''),
                    remarks=row.get('remarks', '')
                )
                records_to_create.append(record)
                existing_records[record_key] = True
                
            except Exception as e:
                continue
        
        # Bulk create records
        records_created = 0
        if records_to_create:
            AttendanceRecord.objects.bulk_create(records_to_create, ignore_conflicts=True)
            records_created = len(records_to_create)
        
        total_records = AttendanceRecord.objects.count()
        
        return records_created, duplicates, total_records
        
    except Exception as e:
        raise Exception(f"Error processing Excel file: {str(e)}")

def generate_attendance_log(date, employee):
    """
    Generate attendance log for an employee on a specific date
    Returns first in and last out times
    """
    try:
        # Get all attendance records for the employee on the date
        records = AttendanceRecord.objects.filter(
            employee=employee,
            timestamp__date=date,
            is_active=True
        ).order_by('timestamp')
        
        if not records.exists():
            return None, None
        
        # Get first and last records
        first_record = records.first()
        last_record = records.last()
        
        first_in = first_record.timestamp.time()
        last_out = last_record.timestamp.time()
        
        return first_in, last_out
    
    except Exception as e:
        print(f"Error generating attendance log: {str(e)}")
        return None, None

def process_daily_attendance(date=None):
    """
    Process attendance records and create attendance logs for all employees
    """
    if date is None:
        date = timezone.now().date()
    
    try:
        # Get all employees with attendance records for the date
        employees = Employee.objects.filter(
            attendance_records__timestamp__date=date,
            attendance_records__is_active=True
        ).distinct()
        
        logs_created = 0
        
        for employee in employees:
            first_in, last_out = generate_attendance_log(date, employee)
            
            if first_in and last_out:
                # Create or update attendance log
                AttendanceLog.objects.update_or_create(
                    employee=employee,
                    date=date,
                    defaults={
                        'first_in_time': first_in,
                        'last_out_time': last_out,
                        'source': 'system'
                    }
                )
                logs_created += 1
        
        return logs_created
    
    except Exception as e:
        raise Exception(f"Error processing daily attendance: {str(e)}")

def validate_attendance_edit(original_log, edited_in_time, edited_out_time):
    """
    Validate attendance edit times
    """
    try:
        # Convert string times to time objects if necessary
        if isinstance(edited_in_time, str):
            edited_in_time = datetime.strptime(edited_in_time, '%H:%M').time()
        if isinstance(edited_out_time, str):
            edited_out_time = datetime.strptime(edited_out_time, '%H:%M').time()
        
        # Basic validation
        if edited_in_time > edited_out_time:
            raise ValueError("First in time cannot be after last out time")
        
        # Check if times are within 24 hours
        time_diff = datetime.combine(datetime.today(), edited_out_time) - \
                   datetime.combine(datetime.today(), edited_in_time)
        
        if time_diff > timedelta(hours=24):
            raise ValueError("Time difference cannot be more than 24 hours")
        
        return True
        
    except Exception as e:
        raise ValueError(f"Invalid time format or values: {str(e)}")

def get_attendance_summary(employee, start_date, end_date):
    """
    Get attendance summary for an employee within a date range
    """
    logs = AttendanceLog.objects.filter(
        employee=employee,
        date__range=(start_date, end_date),
        is_active=True
    ).order_by('date')
    
    summary = {
        'total_days': (end_date - start_date).days + 1,
        'present_days': logs.count(),
        'absent_days': 0,
        'leave_days': 0,
        'holidays': 0,
        'attendance_details': []
    }
    
    for log in logs:
        summary['attendance_details'].append({
            'date': log.date,
            'first_in': log.first_in_time,
            'last_out': log.last_out_time,
            'source': log.source
        })
    
    return summary