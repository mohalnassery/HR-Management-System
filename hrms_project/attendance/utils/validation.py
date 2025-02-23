from datetime import datetime
from typing import List, Optional, Any, Dict
from rest_framework.exceptions import ValidationError
import logging

logger = logging.getLogger('attendance')

class RequestValidator:
    """Centralized request validation utilities"""
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str, fmt: str = '%Y-%m-%d') -> Dict[str, datetime]:
        """
        Validate and parse date range parameters.
        
        Args:
            start_date: Start date string
            end_date: End date string
            fmt: Date string format
            
        Returns:
            Dictionary with parsed start_date and end_date
            
        Raises:
            ValidationError: If dates are invalid or start_date > end_date
        """
        logger.debug(f"Validating date range: start={start_date}, end={end_date}")
        
        if not start_date or not end_date:
            logger.error("Missing date parameters")
            raise ValidationError("Both start_date and end_date are required")
        
        try:
            parsed_start = datetime.strptime(start_date, fmt)
            parsed_end = datetime.strptime(end_date, fmt)
            logger.debug(f"Parsed dates: start={parsed_start}, end={parsed_end}")
        except ValueError:
            logger.error(f"Invalid date format. Expected {fmt}")
            raise ValidationError(f"Invalid date format. Use {fmt}")
        
        if parsed_start > parsed_end:
            logger.error("Start date is after end date")
            raise ValidationError("Start date must be before end date")
            
        return {
            'start_date': parsed_start,
            'end_date': parsed_end
        }

    @staticmethod
    def validate_list_param(params: dict, param_name: str, coerce_type: type = str) -> Optional[List]:
        """
        Validate and parse list parameters from request.
        Handles both single values and lists with [] suffix.
        
        Args:
            params: Request parameters dictionary
            param_name: Name of the parameter to validate
            coerce_type: Type to convert values to
            
        Returns:
            List of values or None if parameter not provided
            
        Example:
            >>> # For params like departments[] or departments
            >>> departments = validate_list_param(request.query_params, 'departments', int)
        """
        logger.debug(f"Validating list parameter: {param_name}")
        
        # Try array notation first (e.g. departments[])
        values = params.getlist(f'{param_name}[]', [])
        if not values or not values[0]:
            # Try single param that might be comma-separated
            values = params.getlist(param_name, [])
            
        if not values or not values[0]:
            logger.debug(f"No values provided for {param_name}")
            return None
            
        try:
            result = [coerce_type(v.strip()) for v in values if v.strip()]
            logger.debug(f"Validated {param_name}: {result}")
            return result
        except (ValueError, TypeError):
            logger.error(f"Invalid {param_name} values. Expected {coerce_type.__name__} values.")
            raise ValidationError(
                f"Invalid {param_name} values. Expected {coerce_type.__name__} values."
            )

    @staticmethod
    def validate_report_params(params: dict, optional_params: Optional[List[str]] = None) -> Dict:
        """
        Validate common report parameters.
        
        Args:
            params: Request parameters dictionary
            optional_params: List of optional parameter names to extract
            
        Returns:
            Dictionary of validated parameters
            
        Example:
            >>> validated = validate_report_params(
            ...     request.query_params, 
            ...     ['departments', 'employees', 'status']
            ... )
        """
        logger.debug("Validating report parameters")
        
        # Validate required date range
        validated = RequestValidator.validate_date_range(
            params.get('start_date'),
            params.get('end_date')
        )
        
        # Process optional parameters if specified
        if optional_params:
            param_configs = {
                'departments': (int, 'Department IDs'),
                'employees': (int, 'Employee IDs'),
                'status': (str, 'Status values'),
                'leave_types': (str, 'Leave type codes')
            }
            
            for param in optional_params:
                if param in param_configs:
                    coerce_type, description = param_configs[param]
                    values = RequestValidator.validate_list_param(params, param, coerce_type)
                    if values:
                        validated[param] = values
        
        logger.debug(f"Validated report parameters: {validated}")
        return validated

class ModelValidator:
    """Validation utilities for model operations"""
    
    @staticmethod
    def validate_date_not_past(date_value: datetime, field_name: str = 'date'):
        """Validate that a date is not in the past"""
        logger.debug(f"Validating date not past: {field_name}={date_value}")
        
        if date_value and date_value.date() < datetime.now().date():
            logger.error(f"{field_name} is in the past")
            raise ValidationError({field_name: "Date cannot be in the past"})

    @staticmethod
    def validate_positive_integer(value: int, field_name: str):
        """Validate that a value is a positive integer"""
        logger.debug(f"Validating positive integer: {field_name}={value}")
        
        if value and value < 0:
            logger.error(f"{field_name} is not positive")
            raise ValidationError({field_name: "Value must be positive"})

    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime):
        """Validate a date range is valid"""
        logger.debug(f"Validating date range: start={start_date}, end={end_date}")
        
        if start_date and end_date and start_date > end_date:
            logger.error("End date is before start date")
            raise ValidationError({
                'end_date': "End date must be after start date"
            })
