from django.utils.html import format_html
from django.utils.safestring import mark_safe
from typing import Dict, Any, Optional
from datetime import date, time, datetime

class DisplayFormatter:
    """Centralized display formatting utilities for consistent UI presentation"""
    
    @staticmethod
    def color_coded_display(value: Any, display_value: str, color_map: Dict[str, str]) -> str:
        """
        Generate color-coded HTML display for values.
        
        Args:
            value: The value to look up in the color map
            display_value: The text to display
            color_map: Dictionary mapping values to colors
            
        Returns:
            HTML formatted string with colored span
        
        Example:
            >>> color_map = {'active': 'green', 'inactive': 'red'}
            >>> DisplayFormatter.color_coded_display('active', 'Active', color_map)
            '<span style="color: green;">Active</span>'
        """
        color = color_map.get(str(value), 'gray')
        return format_html('<span style="color: {};">{}</span>', color, display_value)
    
    @staticmethod
    def timing_display(start_time: Optional[time], end_time: Optional[time], title: str = '') -> str:
        """
        Format time range for display.
        
        Args:
            start_time: Starting time
            end_time: Ending time
            title: Optional hover title for the time range
            
        Returns:
            HTML formatted string showing time range
        """
        if not (start_time and end_time):
            return format_html('<span class="text-muted">Not set</span>')
        
        time_str = f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"
        if title:
            return format_html('<span title="{}">{}</span>', title, time_str)
        return format_html('<span>{}</span>', time_str)

    @staticmethod
    def period_display(start_date: date, end_date: Optional[date] = None, is_permanent: bool = False) -> str:
        """
        Format date period for display.
        
        Args:
            start_date: Period start date
            end_date: Optional period end date
            is_permanent: Whether the period is permanent
            
        Returns:
            Formatted string showing date period
        """
        start = start_date.strftime('%b %d, %Y')
        if end_date:
            if is_permanent:
                return f"From {start} (Permanent)"
            return f"{start} - {end_date.strftime('%b %d, %Y')}"
        return f"From {start}"

    @staticmethod
    def duration_display(duration_minutes: int, show_zero: bool = True) -> str:
        """
        Format duration in minutes for display.
        
        Args:
            duration_minutes: Duration in minutes
            show_zero: Whether to show zero durations
            
        Returns:
            Formatted string showing duration
        """
        if duration_minutes == 0 and not show_zero:
            return ''
            
        hours = duration_minutes // 60
        minutes = duration_minutes % 60
        
        if hours and minutes:
            return f"{hours}h {minutes}m"
        elif hours:
            return f"{hours}h"
        return f"{minutes}m"

# Common color maps used across the application
STATUS_COLORS = {
    'present': 'green',
    'absent': 'red',
    'late': 'orange',
    'leave': 'blue',
    'holiday': 'purple'
}

SHIFT_TYPE_COLORS = {
    'DEFAULT': 'green',
    'NIGHT': 'purple',
    'OPEN': 'blue'
}
