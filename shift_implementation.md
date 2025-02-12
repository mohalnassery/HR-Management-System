# Shift Implementation Workflow

## 1. Shift Types & Configuration

### Default Shift (7:00 AM - 4:00 PM)
- Fixed timing: **7:00 AM to 4:00 PM**
- **1-hour break** automatically deducted
- **Grace period:** 15 minutes
- **Total expected hours:** 8 (9 hours - 1-hour break)

### Open Shift (Flexible)
- **No fixed timing**
- **1-hour break** automatically deducted
- **Grace period:** 15 minutes
- **Total expected hours:** 8 (9 hours - 1-hour break)

### Night Shift (7:00 PM - 4:00 AM)
- Default timing: **7:00 PM to 4:00 AM** (next day)
- Supports timing override through `DateSpecificShiftOverride`
- **1-hour break** automatically deducted
- **Grace period:** 15 minutes
- **Total expected hours:** 8 (9 hours - 1-hour break)

---

## 2. Database Structure

### Shift Model
```python
class Shift(models.Model):
    name = models.CharField(max_length=100)
    shift_type = models.CharField(choices=[
        ('DEFAULT', 'Default Shift (7AM-4PM)'),
        ('NIGHT', 'Night Shift'),
        ('OPEN', 'Open Shift')
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_duration = models.PositiveIntegerField(default=60) # minutes
    grace_period = models.PositiveIntegerField(default=15) # minutes
```

### DateSpecificShiftOverride Model (for Night Shift)
```python
class DateSpecificShiftOverride(models.Model):
    date = models.DateField(unique=True)
    shift_type = models.CharField(default='NIGHT')
    override_start_time = models.TimeField(null=True)
    override_end_time = models.TimeField(null=True)
```

---

## 3. Work Duration Calculation

### Regular Shifts (Default & Open)
1. Get first check-in and last check-out.
2. Calculate total duration: `last_out - first_in`.
3. Deduct **1-hour break**.
4. Store total work minutes.

### Night Shift
1. Get first check-in and last check-out.
2. If check-out time **<** check-in time:
   - Add **24 hours** to check-out time.
3. Calculate total duration.
4. Deduct **1-hour break**.
5. Store total work minutes.

---

## 4. Lateness Calculation

### For All Shifts
1. Compare first check-in with **shift start time + grace period**.
2. If late:
   - Calculate **late minutes**.
   - Mark attendance as **'late'**.
   - Store late minutes.

### Night Shift Special Handling
1. Check if check-in is **after midnight**.
2. Compare with **previous day's shift start** if needed.
3. Apply **grace period**.
4. Calculate lateness if applicable.

---

## 5. Implementation Steps

### 1. Initialize Default Shifts:
```python
DEFAULT_SHIFTS = [
    {
        'name': 'Default Shift',
        'shift_type': 'DEFAULT',
        'start_time': time(7, 0), # 7:00 AM
        'end_time': time(16, 0), # 4:00 PM
        'break_duration': 60,
        'grace_period': 15
    },
    {
        'name': 'Night Shift',
        'shift_type': 'NIGHT',
        'start_time': time(19, 0), # 7:00 PM
        'end_time': time(4, 0), # 4:00 AM
        'break_duration': 60,
        'grace_period': 15
    },
    {
        'name': 'Open Shift',
        'shift_type': 'OPEN',
        'start_time': time(8, 0), # Default 8:00 AM
        'end_time': time(17, 0), # Default 5:00 PM
        'break_duration': 60,
        'grace_period': 15
    }
]
```

### 2. Create Night Shift Override (when needed):
```python
DateSpecificShiftOverride.objects.create(
    date=date.today(),
    shift_type='NIGHT',
    override_start_time=time(20, 0), # 8:00 PM
    override_end_time=time(5, 0) # 5:00 AM
)
```

---

## 6. Key Features

1. **Automatic break deduction**
2. **Grace period handling**
3. **Night shift cross-day support**
4. **Flexible shift override system**
5. **Late calculation with grace period**
6. **Work duration calculation**

---

## 7. Usage Example

### Calculate Work Duration for Night Shift
```python
if shift.shift_type == 'NIGHT' and shift.end_time < shift.start_time:
    if last_out.time() < first_in.time():
        # Add one day to last_out for correct duration calculation
        last_out += timedelta(days=1)
    
    # Calculate base duration
    duration = int((last_out - first_in).total_seconds() / 60) # Convert to minutes
    
    # Deduct break
    duration -= shift.break_duration
```
