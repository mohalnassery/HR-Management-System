from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Tuple, Dict, Any, Optional
from django.db.models import Q
from django.utils import timezone

from ..models import (
    Leave, LeaveType, LeaveBalance, LeaveBalanceTier,
    Employee, Holiday, AttendanceLog, LeaveBeginningBalance
)

class LeaveRuleService:
    """Service for handling leave request validation and rules"""
    
    @classmethod
    def validate_leave_request(
        cls,
        employee: Employee,
        leave_type: LeaveType,
        sub_type: str,
        start_date: date,
        end_date: date
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate a leave request based on leave type rules
        
        Args:
            employee: The employee requesting leave
            leave_type: The type of leave being requested
            sub_type: The sub-type of leave (if applicable)
            start_date: The start date of the leave
            end_date: The end date of the leave
            
        Returns:
            Tuple containing:
            - bool: Whether the request is valid
            - str: Message explaining the validation result
            - dict: Additional data (e.g., available balance)
        """
        # Get the appropriate validator based on leave type
        validator = cls._get_validator(leave_type.code)
        return validator(employee, leave_type, sub_type, start_date, end_date)
    
    @classmethod
    def _get_validator(cls, leave_type_code: str):
        """Return appropriate validator function based on leave type"""
        validators = {
            'ANNUAL': cls._validate_annual_leave,
            'HALF': cls._validate_annual_leave,  # Uses same balance as annual
            'SICK': cls._validate_sick_leave,
            'HAJJ': cls._validate_hajj_leave,
            'DEATH': cls._validate_death_leave,
            'MARRIAGE': cls._validate_fixed_duration_leave,
            'PATERNITY': cls._validate_fixed_duration_leave,
            'MATERNITY': cls._validate_maternity_leave,
            'IDDAH': cls._validate_iddah_leave,
            'INJURY': cls._validate_injury_leave,
            'EMERG': cls._validate_emergency_leave,
            'PERMISSION': cls._validate_permission_leave
        }
        return validators.get(leave_type_code, cls._validate_default)
    
    @classmethod
    def _validate_annual_leave(
        cls,
        employee: Employee,
        leave_type: LeaveType,
        sub_type: str,
        start_date: date,
        end_date: date
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate annual or half-day leave request"""
        # Calculate duration based on sub-type
        if sub_type in ['half_day', 'morning', 'afternoon']:
            duration = Decimal('0.5')
        else:
            duration = cls._calculate_leave_duration(start_date, end_date)
            
        # Get beginning balance
        beginning_balance = LeaveBeginningBalance.objects.filter(
            employee=employee,
            leave_type=leave_type
        ).order_by('-as_of_date').first()
        
        initial_balance = beginning_balance.balance_days if beginning_balance else 0
        
        # Get beginning date (try join_date first, then beginning balance, then default to Jan 1st)
        if beginning_balance:
            start_date_calc = beginning_balance.as_of_date
        else:
            # Try to get join_date if it exists
            if hasattr(employee, 'join_date') and employee.join_date:
                start_date_calc = employee.join_date
            else:
                # Default to January 1st of current year
                current_year = date.today().year
                start_date_calc = date(current_year, 1, 1)
        
        end_date_calc = date.today()
        
        try:
            # Get holidays for the period
            holiday_dates = set(Holiday.objects.filter(
                date__range=[start_date_calc, end_date_calc]
            ).values_list('date', flat=True))
            
            # Get attendance logs for the period
            attendance_logs = set(AttendanceLog.objects.filter(
                employee=employee,
                date__range=[start_date_calc, end_date_calc],
                status='present'
            ).values_list('date', flat=True))
            
            # Count Fridays that should be included
            friday_count = 0
            current_date = start_date_calc
            while current_date <= end_date_calc:
                if current_date.weekday() == 4:  # Friday
                    thursday = current_date - timedelta(days=1)
                    saturday = current_date + timedelta(days=1)
                    
                    # Check if Thursday or Saturday was attended or was a holiday
                    thursday_attended = thursday in attendance_logs or thursday in holiday_dates
                    saturday_attended = saturday in attendance_logs or saturday in holiday_dates
                    
                    if thursday_attended or saturday_attended:
                        friday_count += 1
                
                current_date += timedelta(days=1)
            
            # Calculate total working days including valid Fridays and holidays
            total_working_days = Decimal(len(attendance_logs) + friday_count + len(holiday_dates))
            
            # Calculate monthly rate (2.5 days per month, assuming 30 working days per month)
            daily_rate = Decimal('2.5') / Decimal('30')
            
            # Calculate accrued leave
            accrued_days = total_working_days * daily_rate
            
            # Get used days from balance
            balance = LeaveBalance.objects.filter(
                employee=employee,
                leave_type=leave_type,
                is_active=True
            ).first()
            
            used_days = balance.used_days if balance else Decimal('0')
            pending_days = balance.pending_days if balance else Decimal('0')
            
            # Calculate total and remaining days
            total_days = Decimal(initial_balance) + accrued_days
            remaining_days = total_days - used_days - pending_days
            
            # Check if sufficient balance
            if remaining_days < duration:
                return False, f"Insufficient balance. Available: {remaining_days:.2f} days", {
                    'available_balance': remaining_days,
                    'requested_duration': duration,
                    'total_days': total_days,
                    'used_days': used_days,
                    'pending_days': pending_days,
                    'accrued_days': accrued_days
                }
                
            return True, "Leave can be taken", {
                'available_balance': remaining_days,
                'requested_duration': duration,
                'total_days': total_days,
                'used_days': used_days,
                'pending_days': pending_days,
                'accrued_days': accrued_days,
                'is_paid': True
            }
            
        except Exception as e:
            print(f"Error in leave calculation: {str(e)}")
            # If there's an error in calculation, use defaults from balance
            balance = LeaveBalance.objects.filter(
                employee=employee,
                leave_type=leave_type,
                is_active=True
            ).first()
            
            if not balance:
                return False, "No leave balance found", {}
                
            if balance.available_days < duration:
                return False, f"Insufficient balance. Available: {balance.available_days:.2f} days", {
                    'available_balance': balance.available_days,
                    'requested_duration': duration
                }
                
            return True, "Leave can be taken", {
                'available_balance': balance.available_days,
                'requested_duration': duration,
                'is_paid': True
            }
    
    @classmethod
    def _validate_sick_leave(
        cls,
        employee: Employee,
        leave_type: LeaveType,
        sub_type: str,
        start_date: date,
        end_date: date
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate sick leave request with tier progression"""
        duration = cls._calculate_leave_duration(start_date, end_date)
        
        # Get sick leave balance and tiers
        balance = LeaveBalance.objects.filter(
            employee=employee,
            leave_type__code='SICK',
            is_active=True
        ).first()
        
        if not balance:
            return False, "No sick leave balance found", {}
            
        tiers = LeaveBalanceTier.objects.filter(
            balance=balance
        ).order_by('tier_number')
        
        if not tiers.exists():
            # Create tiers if they don't exist
            tiers = [
                LeaveBalanceTier.objects.create(
                    balance=balance,
                    tier_number=1,
                    tier_name='Full Pay',
                    days_allowed=15,
                    pay_percentage=100
                ),
                LeaveBalanceTier.objects.create(
                    balance=balance,
                    tier_number=2,
                    tier_name='Half Pay',
                    days_allowed=20,
                    pay_percentage=50
                ),
                LeaveBalanceTier.objects.create(
                    balance=balance,
                    tier_number=3,
                    tier_name='No Pay',
                    days_allowed=20,
                    pay_percentage=0
                )
            ]
        
        # Find available tier
        available_tier = None
        for tier in tiers:
            if tier.days_used < tier.days_allowed:
                available_tier = tier
                break
                
        if not available_tier:
            return False, "All sick leave tiers exhausted", {
                'tiers': [
                    {
                        'name': tier.tier_name,
                        'used': tier.days_used,
                        'allowed': tier.days_allowed
                    }
                    for tier in tiers
                ]
            }
            
        # Check if requested duration fits in current tier
        remaining_in_tier = available_tier.days_allowed - available_tier.days_used
        if duration > remaining_in_tier:
            return False, f"Requested duration exceeds available days in {available_tier.tier_name} tier", {
                'available_days': remaining_in_tier,
                'requested_duration': duration,
                'tier': available_tier.tier_name
            }
            
        return True, f"Leave can be taken using {available_tier.tier_name} tier", {
            'available_days': remaining_in_tier,
            'requested_duration': duration,
            'tier': available_tier.tier_name
        }
    
    @classmethod
    def _validate_hajj_leave(
        cls,
        employee: Employee,
        leave_type: LeaveType,
        sub_type: str,
        start_date: date,
        end_date: date
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate Hajj leave (once during employment)"""
        # Check if employee has taken Hajj leave before
        previous_hajj = Leave.objects.filter(
            employee=employee,
            leave_type__code='HAJJ',
            status__in=['approved', 'pending'],
            is_active=True
        ).exists()
        
        if previous_hajj:
            return False, "Hajj leave can only be taken once during employment", {}
            
        # Validate duration
        duration = cls._calculate_leave_duration(start_date, end_date)
        if duration > 14:  # Hajj leave is fixed at 14 days
            return False, "Hajj leave cannot exceed 14 days", {
                'allowed_duration': 14,
                'requested_duration': duration
            }
            
        return True, "Hajj leave can be taken", {
            'allowed_duration': 14,
            'requested_duration': duration
        }
    
    @classmethod
    def _validate_death_leave(
        cls,
        employee: Employee,
        leave_type: LeaveType,
        sub_type: str,
        start_date: date,
        end_date: date
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate death (compassionate) leave"""
        # Get allowed duration based on sub-type
        allowed_duration = {
            'spouse_30': 30,  # woman's husband
            'spouse_3': 3,    # man's wife
            'first_degree': 3,
            'second_degree': 3
        }.get(sub_type)
        
        if not allowed_duration:
            return False, "Invalid death leave sub-type", {}
            
        duration = cls._calculate_leave_duration(start_date, end_date)
        if duration > allowed_duration:
            return False, f"Death leave cannot exceed {allowed_duration} days for this type", {
                'allowed_duration': allowed_duration,
                'requested_duration': duration
            }
            
        return True, "Death leave can be taken", {
            'allowed_duration': allowed_duration,
            'requested_duration': duration
        }
    
    @classmethod
    def _validate_maternity_leave(
        cls,
        employee: Employee,
        leave_type: LeaveType,
        sub_type: str,
        start_date: date,
        end_date: date
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate maternity leave request"""
        # Check gender
        if employee.gender != 'F':
            return False, "Maternity leave is only available for female employees", {}

        # Validate duration based on sub-type
        duration = cls._calculate_leave_duration(start_date, end_date)
        if sub_type == 'paid_60':
            if duration != 60:
                return False, "Paid maternity leave must be exactly 60 days", {
                    'allowed_duration': 60,
                    'requested_duration': duration
                }
        elif sub_type == 'unpaid_15':
            if duration != 15:
                return False, "Additional unpaid maternity leave must be exactly 15 days", {
                    'allowed_duration': 15,
                    'requested_duration': duration
                }
        else:
            return False, "Invalid maternity leave sub-type", {}

        return True, "Maternity leave can be taken", {
            'requested_duration': duration,
            'is_paid': sub_type == 'paid_60'
        }
    
    @classmethod
    def _validate_iddah_leave(
        cls,
        employee: Employee,
        leave_type: LeaveType,
        sub_type: str,
        start_date: date,
        end_date: date
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate Iddah leave request"""
        # Check gender
        if employee.gender != 'F':
            return False, "Iddah leave is only available for female employees", {}

        # Validate duration based on sub-type
        duration = cls._calculate_leave_duration(start_date, end_date)
        if sub_type == 'paid_30':
            if duration != 30:
                return False, "Paid Iddah leave must be exactly 30 days", {
                    'allowed_duration': 30,
                    'requested_duration': duration
                }
        elif sub_type == 'unpaid_100':
            if duration != 100:
                return False, "Unpaid Iddah leave must be exactly 100 days", {
                    'allowed_duration': 100,
                    'requested_duration': duration
                }
        else:
            return False, "Invalid Iddah leave sub-type", {}

        return True, "Iddah leave can be taken", {
            'requested_duration': duration,
            'is_paid': sub_type == 'paid_30'
        }
    
    @classmethod
    def _validate_injury_leave(
        cls,
        employee: Employee,
        leave_type: LeaveType,
        sub_type: str,
        start_date: date,
        end_date: date
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate injury leave request"""
        duration = cls._calculate_leave_duration(start_date, end_date)
        if duration > 180:  # Maximum as per Social Insurance Law
            return False, "Injury leave cannot exceed 180 days", {
                'allowed_duration': 180,
                'requested_duration': duration
            }
        return True, "Injury leave can be taken", {'requested_duration': duration}
    
    @classmethod
    def _validate_emergency_leave(
        cls,
        employee: Employee,
        leave_type: LeaveType,
        sub_type: str,
        start_date: date,
        end_date: date
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate emergency leave request"""
        duration = cls._calculate_leave_duration(start_date, end_date)
        if duration > 5:  # Maximum emergency leave days
            return False, "Emergency leave cannot exceed 5 days", {
                'allowed_duration': 5,
                'requested_duration': duration
            }
        return True, "Emergency leave can be taken", {'requested_duration': duration}
    
    @classmethod
    def _validate_permission_leave(
        cls,
        employee: Employee,
        leave_type: LeaveType,
        sub_type: str,
        start_date: date,
        end_date: date
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate permission leave request"""
        duration = cls._calculate_leave_duration(start_date, end_date)
        if duration > 3:  # Maximum permission leave days
            return False, "Permission leave cannot exceed 3 days", {
                'allowed_duration': 3,
                'requested_duration': duration
            }
        if duration < 0.5:  # Minimum half day
            return False, "Permission leave must be at least half day", {
                'min_duration': 0.5,
                'requested_duration': duration
            }
        return True, "Permission leave can be taken", {'requested_duration': duration}
    
    @classmethod
    def _validate_fixed_duration_leave(
        cls,
        employee: Employee,
        leave_type: LeaveType,
        sub_type: str,
        start_date: date,
        end_date: date
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate fixed duration leaves (Marriage, Paternity)"""
        duration = cls._calculate_leave_duration(start_date, end_date)
        allowed_duration = leave_type.days_allowed

        if duration != allowed_duration:
            return False, f"{leave_type.name} must be exactly {allowed_duration} days", {
                'allowed_duration': allowed_duration,
                'requested_duration': duration
            }

        # Check gender for paternity leave
        if leave_type.code == 'PATERNITY' and employee.gender != 'M':
            return False, "Paternity leave is only available for male employees", {}

        return True, f"{leave_type.name} can be taken", {'requested_duration': duration}
    
    @classmethod
    def _validate_default(
        cls,
        employee: Employee,
        leave_type: LeaveType,
        sub_type: str,
        start_date: date,
        end_date: date
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Default validator for leave types without special rules"""
        duration = cls._calculate_leave_duration(start_date, end_date)
        
        # Check if duration matches any fixed duration sub-type
        if sub_type:
            try:
                allowed_days = int(sub_type.split('_')[0])
                if duration != allowed_days:
                    return False, f"Leave duration must be exactly {allowed_days} days", {
                        'allowed_duration': allowed_days,
                        'requested_duration': duration
                    }
            except (ValueError, IndexError):
                pass
        
        return True, "Leave can be taken", {
            'requested_duration': duration
        }
    
    @staticmethod
    def _calculate_leave_duration(start_date: date, end_date: date) -> Decimal:
        """Calculate leave duration excluding holidays"""
        duration = (end_date - start_date).days + 1
        
        # Subtract holidays
        holidays = Holiday.objects.filter(
            date__range=[start_date, end_date],
            is_active=True
        ).count()
        
        return Decimal(str(duration - holidays)) 