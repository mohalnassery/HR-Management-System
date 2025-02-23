from typing import List, Dict, Any
from datetime import datetime, date
import pandas as pd
from django.db import transaction
from attendance.models import AttendanceRecord, AttendanceLog

def process_attendance_excel(file_obj) -> tuple:
    """
    Process uploaded Excel file containing attendance data
    Expected columns: Date And Time, Personnel ID, First Name, Last Name, Card Number,
                     Device Name, Event Point, Verify Type, In/Out Status, Event Description, Remarks
    Returns: records_created, duplicates, total_records, new_employees, unique_dates
    """
    from employees.models import Employee
    
    try:
        # Read Excel file
        df = pd.read_excel(file_obj)
        
        # Verify required columns exist
        required_columns = ['Date And Time', 'Personnel ID']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Initialize counters
        records_created = 0
        duplicates = 0
        new_employees = 0
        unique_dates = set()
        
        # Process the DataFrame and create records
        for _, row in df.iterrows():
            try:
                # Convert date_and_time to datetime
                timestamp = pd.to_datetime(row['Date And Time'])
                employee_id = str(row['Personnel ID'])  # Convert to string to handle numeric IDs
                
                # Try to find the employee, skip if not found
                try:
                    employee = Employee.objects.get(employee_number=employee_id)
                except Employee.DoesNotExist:
                    print(f"Employee not found: {employee_id}")
                    continue
                
                # Add date to unique dates set
                unique_dates.add(timestamp.date())
                
                # Check for duplicate record
                if AttendanceRecord.objects.filter(
                    employee=employee,
                    timestamp=timestamp
                ).exists():
                    duplicates += 1
                    continue
                
                # Create the record
                AttendanceRecord.objects.create(
                    employee=employee,
                    timestamp=timestamp,
                    device_name=row.get('Device Name', ''),
                    event_point=row.get('Event Point', ''),
                    verify_type=row.get('Verify Type', ''),
                    event_description=row.get('Event Description', ''),
                    remarks=row.get('Remarks', '')
                )
                records_created += 1
                
            except Exception as row_error:
                print(f"Error processing row: {row_error}")
                continue
        
        return records_created, duplicates, len(df), new_employees, unique_dates
        
    except Exception as e:
        raise ValueError(f"Error processing Excel file: {str(e)}")

def process_daily_attendance(date_to_process: date) -> int:
    """
    Process attendance records for a specific date and create attendance logs
    Returns the number of logs created/updated
    """
    from django.db.models import Min, Max
    
    logs_processed = 0
    
    with transaction.atomic():
        # Get all records for the specified date grouped by employee
        employee_records = AttendanceRecord.objects.filter(
            timestamp__date=date_to_process,
            is_active=True
        ).values('employee').annotate(
            first_in=Min('timestamp'),
            last_out=Max('timestamp')
        )
        
        # Process each employee's records
        for record in employee_records:
            employee_id = record['employee']
            first_in = record['first_in']
            last_out = record['last_out']
            
            # Get or create the attendance log
            log, created = AttendanceLog.objects.get_or_create(
                employee_id=employee_id,
                date=date_to_process,
                defaults={
                    'first_in_time': first_in.time(),
                    'last_out_time': last_out.time() if last_out else None,
                    'status': 'present',
                    'source': 'system'
                }
            )
            
            if not created:
                # Update existing log
                log.first_in_time = first_in.time()
                log.last_out_time = last_out.time() if last_out else None
                log.status = 'present'
                log.save()
            
            logs_processed += 1
    
    return logs_processed

def get_attendance_summary(start_date: date, end_date: date, employee_id: int = None) -> Dict[str, Any]:
    """
    Get attendance summary for a date range and optionally for a specific employee
    """
    query = AttendanceLog.objects.filter(date__range=(start_date, end_date))
    if employee_id:
        query = query.filter(employee_id=employee_id)
    
    summary = {
        'total_days': (end_date - start_date).days + 1,
        'present_days': query.count(),
        'absent_days': 0,  # Calculate based on business logic
        'late_days': query.filter(is_late=True).count(),
        'early_departure_days': query.filter(left_early=True).count(),
    }
    
    return summary
