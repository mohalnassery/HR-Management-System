# Leave Balance Calculation Fix

## Issue
There is an AttributeError in the leave request creation view where it attempts to access a non-existent field `default_days` on the LeaveType model.

Error details:
```
AttributeError at /attendance/leave_request_create/
'LeaveType' object has no attribute 'default_days'
```

Location: `attendance/views/leave_views.py`, line 137

## Analysis
1. The view is trying to calculate leave balance percentages for progress bars
2. It's using `balance.leave_type.default_days` but this field doesn't exist
3. The LeaveType model uses `days_allowed` instead
4. The calculation also uses `balance_days` when it should use `available_days` for more accurate representation

## Required Changes

### 1. Update Field Reference
Change from using non-existent `default_days` to using `days_allowed`:
```python
# Before
total_allocation = balance.leave_type.default_days

# After
total_allocation = balance.leave_type.days_allowed
```

### 2. Improve Balance Percentage Calculation
Update to use `available_days` instead of `balance_days`:
```python
# Before
balance.balance_percentage = (balance.balance_days / total_allocation) * 100

# After
balance.balance_percentage = (balance.available_days / total_allocation) * 100
```

This change will show the actual available balance percentage rather than the total balance.

## Implementation Plan
1. Switch to Code mode
2. Apply the changes to `leave_views.py`
3. Add tests to verify the balance percentage calculation
4. Test the leave request form to ensure proper display

## Next Steps
1. Review and approve this plan
2. Switch to Code mode for implementation
3. Test the changes
4. Document any additional improvements needed