from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from typing import List
import logging

from ..utils.validation import RequestValidator
from ..services.report_generator import ReportGeneratorFactory

logger = logging.getLogger('attendance')

class ReportViewSet(viewsets.ViewSet):
    """ViewSet for handling report generation and exports"""
    
    permission_classes = [IsAuthenticated]

    def _handle_report_request(
        self,
        report_type: str,
        request_params: dict,
        optional_params: List[str],
        export_format: str = None
    ):
        """
        Handle report generation request
        
        Args:
            report_type: Type of report to generate
            request_params: Request parameters
            optional_params: Optional parameters to validate
            export_format: Optional export format
        """
        try:
            logger.debug(f"Handling report request - Type: {report_type}, Params: {request_params}")
            
            # Validate date range first
            validated_dates = RequestValidator.validate_date_range(
                request_params.get('start_date'),
                request_params.get('end_date')
            )
            logger.debug(f"Validated dates: {validated_dates}")
            
            # Validate optional parameters
            params = {
                'start_date': validated_dates['start_date'],
                'end_date': validated_dates['end_date']
            }
            
            # Add optional parameters if present
            for param in optional_params:
                param_value = RequestValidator.validate_list_param(request_params, param)
                if param_value:
                    params[param] = param_value
            logger.debug(f"Final params after validation: {params}")
            
            # Create report generator
            generator = ReportGeneratorFactory.create(report_type)
            
            # Generate report in requested format (default to json)
            format = export_format if export_format else 'json'
            logger.debug(f"Generating report in {format} format")
            return generator.generate(format, **params)
            
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response(
                {"error": f"Unexpected error: {str(e)}"}, 
                status=500
            )

    @action(detail=False, methods=['get'])
    def attendance(self, request):
        """Generate attendance report"""
        logger.debug("Generating attendance report")
        return self._handle_report_request(
            'attendance',
            request.query_params,
            ['departments', 'employees', 'status']
        )

    @action(detail=False, methods=['get'])
    def leave(self, request):
        """Generate leave report"""
        logger.debug("Generating leave report")
        return self._handle_report_request(
            'leave',
            request.query_params,
            ['departments', 'employees', 'leave_types']
        )

    @action(detail=False, methods=['get']) 
    def holiday(self, request):
        """Generate holiday report"""
        logger.debug("Generating holiday report")
        return self._handle_report_request(
            'holiday',
            request.query_params,
            []
        )

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export report in specified format"""
        logger.debug("Exporting report")
        try:
            report_type = request.query_params.get('type', 'attendance')
            export_format = request.query_params.get('format', 'csv')
            
            optional_params = {
                'attendance': ['departments', 'employees', 'status'],
                'leave': ['departments', 'employees', 'leave_types'],
                'holiday': []
            }.get(report_type, [])
            
            return self._handle_report_request(
                report_type,
                request.query_params,
                optional_params,
                export_format
            )
            
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response(
                {"error": f"Unexpected error: {str(e)}"}, 
                status=500
            )
