"""
Default configurations for shifts.
These can be modified without changing the model code.
"""

# Shift type priorities (higher number = higher priority)
SHIFT_PRIORITIES = {
    'NIGHT': 3,    # Highest priority
    'OPEN': 2,     # Medium priority
    'DEFAULT': 1,  # Lowest priority
}

# Default shift configurations
DEFAULT_SHIFTS = [
    {
        'name': 'Default Shift',
        'shift_type': 'DEFAULT',
        'start_time': '07:00',
        'end_time': '16:00',
        'grace_period': 15,
        'break_duration': 60,
    },
    {
        'name': 'Night Shift',
        'shift_type': 'NIGHT',
        'start_time': '18:00',
        'end_time': '03:00',
        'grace_period': 15,
        'break_duration': 60,
    },
    {
        'name': 'Open Shift',
        'shift_type': 'OPEN',
        'start_time': '00:00',
        'end_time': '23:59',
        'grace_period': 30,
        'break_duration': 60,
    },
]