from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List

from django.db import transaction
from django.utils import timezone

from ..models import RamadanPeriod

class RamadanService:
    @staticmethod
    def get_active_period(date_to_check: Optional[date] = None) -> Optional[RamadanPeriod]:
        """
        Get the active Ramadan period for a given date
        
        Args:
            date_to_check: The date to check (defaults to today)
            
        Returns:
            RamadanPeriod if date falls within an active period, None otherwise
        """
        if not date_to_check:
            date_to_check = timezone.now().date()
            
        return RamadanPeriod.objects.filter(
            start_date__lte=date_to_check,
            end_date__gte=date_to_check,
            is_active=True
        ).first()

    @staticmethod
    def create_period(year: int, start_date: date, end_date: date) -> RamadanPeriod:
        """
        Create a new Ramadan period
        
        Args:
            year: The year of the Ramadan period
            start_date: Start date of Ramadan
            end_date: End date of Ramadan
            
        Returns:
            The created RamadanPeriod instance
            
        Raises:
            ValueError: If dates are invalid or period overlaps with existing ones
        """
        # Validate year matches dates
        if (start_date.year != year or end_date.year != year):
            raise ValueError("Start and end dates must be within the specified year")
            
        # Check for overlaps
        overlapping = RamadanPeriod.objects.filter(
            start_date__lte=end_date,
            end_date__gte=start_date
        ).exists()
        
        if overlapping:
            raise ValueError("This period overlaps with an existing Ramadan period")
            
        return RamadanPeriod.objects.create(
            year=year,
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )

    @staticmethod
    @transaction.atomic
    def update_period(
        period_id: int,
        year: int,
        start_date: date,
        end_date: date,
        is_active: bool
    ) -> RamadanPeriod:
        """
        Update an existing Ramadan period
        
        Args:
            period_id: ID of the period to update
            year: New year
            start_date: New start date
            end_date: New end date
            is_active: New active status
            
        Returns:
            The updated RamadanPeriod instance
            
        Raises:
            ValueError: If dates are invalid or period overlaps with existing ones
            RamadanPeriod.DoesNotExist: If period_id is invalid
        """
        # Validate year matches dates
        if (start_date.year != year or end_date.year != year):
            raise ValueError("Start and end dates must be within the specified year")
            
        # Check for overlaps with other periods
        overlapping = RamadanPeriod.objects.exclude(
            id=period_id
        ).filter(
            start_date__lte=end_date,
            end_date__gte=start_date
        ).exists()
        
        if overlapping:
            raise ValueError("This period overlaps with an existing Ramadan period")
            
        period = RamadanPeriod.objects.get(id=period_id)
        period.year = year
        period.start_date = start_date
        period.end_date = end_date
        period.is_active = is_active
        period.save()
        
        return period

    @staticmethod
    def get_all_periods(include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Get all Ramadan periods with optional filtering
        
        Args:
            include_inactive: Whether to include inactive periods
            
        Returns:
            List of dictionaries containing period details
        """
        queryset = RamadanPeriod.objects.all()
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
            
        return [{
            'id': period.id,
            'year': period.year,
            'start_date': period.start_date,
            'end_date': period.end_date,
            'is_active': period.is_active,
            'duration': (period.end_date - period.start_date).days + 1
        } for period in queryset.order_by('-year')]

    @staticmethod
    def calculate_working_hours(
        normal_hours: float,
        is_ramadan: bool = False
    ) -> float:
        """
        Calculate adjusted working hours for Ramadan
        
        Args:
            normal_hours: Regular working hours
            is_ramadan: Whether the calculation is for Ramadan period
            
        Returns:
            Adjusted working hours
        """
        if not is_ramadan:
            return normal_hours
            
        # Default Ramadan reduction (2 hours less)
        return max(normal_hours - 2, 4)  # Minimum 4 hours

    @staticmethod
    def validate_period_dates(
        start_date: date,
        end_date: date,
        year: int,
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        Validate Ramadan period dates
        
        Args:
            start_date: Proposed start date
            end_date: Proposed end date
            year: Year the period should be in
            exclude_id: Optional ID to exclude from overlap check
            
        Returns:
            True if dates are valid, False otherwise
            
        Raises:
            ValueError with specific error message if validation fails
        """
        # Check year consistency
        if start_date.year != year or end_date.year != year:
            raise ValueError("Start and end dates must be within the specified year")
            
        # Check date order
        if end_date < start_date:
            raise ValueError("End date cannot be before start date")
            
        # Check duration (typical Ramadan is 29-30 days)
        duration = (end_date - start_date).days + 1
        if duration < 28 or duration > 31:
            raise ValueError(f"Duration ({duration} days) seems invalid for Ramadan")
            
        # Check for overlaps
        query = RamadanPeriod.objects.filter(
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        if exclude_id:
            query = query.exclude(id=exclude_id)
            
        if query.exists():
            raise ValueError("This period overlaps with an existing Ramadan period")
            
        return True
