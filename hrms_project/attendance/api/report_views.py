from datetime import datetime
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.http import HttpResponse
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
import io
import xlsxwriter
import csv

from ..models import AttendanceLog, Leave, Holiday
from ..serializers import AttendanceLogSerializer
from ..services.report_service import ReportService
from ..services.pdf_service import PDFReportService

class LargeResultsSetPagination(PageNumberPagination):
    """Custom pagination class for large result sets"""
    page_size = 400
    page_size_query_param = 'page_size'
    max_page_size = 1000

class ReportViewSet(viewsets.ViewSet):
    """ViewSet for handling report generation and exports"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def attendance(self, request):
        """Generate attendance report"""
        try:
            params = self._validate_and_parse_params(request.GET)
            data = ReportService.get_attendance_report(**params)
            return Response(data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
    
    @action(detail=False, methods=['get'])
    def leave(self, request):
        """Generate leave report"""
        try:
            params = self._validate_and_parse_params(request.GET)
            data = ReportService.get_leave_report(**params)
            return Response(data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
    
    @action(detail=False, methods=['get'])
    def holiday(self, request):
        """Generate holiday report"""
        try:
            params = self._validate_and_parse_params(request.GET)
            data = ReportService.get_holiday_report(**params)
            return Response(data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export report in specified format"""
        try:
            params = self._validate_and_parse_params(request.GET)
            report_type = request.GET.get('type', 'attendance')
            export_format = request.GET.get('format', 'csv')
            
            # Get report data based on type
            if report_type == 'attendance':
                data = ReportService.get_attendance_report(**params)
            elif report_type == 'leave':
                data = ReportService.get_leave_report(**params)
            elif report_type == 'holiday':
                data = ReportService.get_holiday_report(**params)
            else:
                raise ValidationError(f"Invalid report type: {report_type}")
            
            # Export in requested format
            if export_format == 'csv':
                return self._export_csv(data, report_type)
            elif export_format == 'excel':
                return self._export_excel(data, report_type)
            elif export_format == 'pdf':
                return self._export_pdf(data, report_type)
            elif export_format == 'json':
                return Response(data)
            else:
                raise ValidationError(f"Invalid export format: {export_format}")
                
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
    
    def _validate_and_parse_params(self, params):
        """Validate and parse request parameters"""
        try:
            # Required parameters
            start_date = datetime.strptime(params.get('start_date', ''), '%Y-%m-%d')
            end_date = datetime.strptime(params.get('end_date', ''), '%Y-%m-%d')
            
            if start_date > end_date:
                raise ValidationError("Start date must be before end date")
            
            # Optional parameters
            result = {
                'start_date': start_date,
                'end_date': end_date
            }
            
            # Parse department IDs
            departments = params.getlist('departments')
            if departments:
                result['departments'] = [int(d) for d in departments]
            
            # Parse employee IDs
            employees = params.getlist('employees')
            if employees:
                result['employees'] = [int(e) for e in employees]
            
            # Parse status filters
            status = params.getlist('status')
            if status:
                result['status'] = status
            
            # Parse leave types for leave reports
            leave_types = params.getlist('leave_types')
            if leave_types:
                result['leave_types'] = leave_types
            
            return result
            
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid parameters: {str(e)}")
    
    def _export_pdf(self, data: dict, report_type: str) -> HttpResponse:
        """Export report as PDF"""
        try:
            if report_type == 'attendance':
                pdf_content = PDFReportService.generate_attendance_report_pdf(data)
                filename = f"attendance_report_{data['start_date'].strftime('%Y%m%d')}.pdf"
            elif report_type == 'leave':
                pdf_content = PDFReportService.generate_leave_report_pdf(data)
                filename = f"leave_report_{data['start_date'].strftime('%Y%m%d')}.pdf"
            elif report_type == 'holiday':
                pdf_content = PDFReportService.generate_holiday_report_pdf(data)
                filename = f"holiday_report_{data['start_date'].strftime('%Y%m%d')}.pdf"
            else:
                raise ValidationError(f"Invalid report type for PDF export: {report_type}")
            
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            raise ValidationError(f"Error generating PDF: {str(e)}")
    
    def _export_csv(self, data: dict, report_type: str) -> HttpResponse:
        """Export report as CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        if report_type == 'attendance':
            # Write summary
            writer.writerow(['Summary'])
            writer.writerow(['Status', 'Count'])
            for status, count in data['summary'].items():
                writer.writerow([status.title(), count])
            
            # Write employee records
            writer.writerow([])
            writer.writerow(['Employee Records'])
            writer.writerow(['ID', 'Name', 'Department', 'Present', 'Absent', 'Late', 'Leave'])
            for record in data['employee_records']:
                writer.writerow([
                    record['id'],
                    record['name'],
                    record['department'],
                    record['present_days'],
                    record['absent_days'],
                    record['late_days'],
                    record['leave_days']
                ])
                
        elif report_type == 'leave':
            # Write leave type statistics
            writer.writerow(['Leave Type Statistics'])
            writer.writerow(['Type', 'Count', 'Average Duration'])
            for stat in data['leave_type_stats']:
                writer.writerow([
                    stat['leave_type'],
                    stat['count'],
                    round(stat['avg_duration'], 2) if stat['avg_duration'] else 0
                ])
                
        elif report_type == 'holiday':
            # Write holidays
            writer.writerow(['Date', 'Name', 'Description', 'Type'])
            for holiday in data['holidays']:
                writer.writerow([
                    holiday['date'],
                    holiday['name'],
                    holiday['description'],
                    holiday['type']
                ])
        
        output.seek(0)
        response = HttpResponse(output.read(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
        return response
    
    def _export_excel(self, data: dict, report_type: str) -> HttpResponse:
        """Export report as Excel"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        if report_type == 'attendance':
            ws = workbook.add_worksheet('Summary')
            # Write summary
            ws.write('A1', 'Summary')
            ws.write('A2', 'Status')
            ws.write('B2', 'Count')
            row = 3
            for status, count in data['summary'].items():
                ws.write(f'A{row}', status.title())
                ws.write(f'B{row}', count)
                row += 1
            
            # Write employee records
            ws = workbook.add_worksheet('Employee Records')
            headers = ['ID', 'Name', 'Department', 'Present', 'Absent', 'Late', 'Leave']
            for col, header in enumerate(headers):
                ws.write(0, col, header)
            
            for row, record in enumerate(data['employee_records'], 1):
                ws.write(row, 0, record['id'])
                ws.write(row, 1, record['name'])
                ws.write(row, 2, record['department'])
                ws.write(row, 3, record['present_days'])
                ws.write(row, 4, record['absent_days'])
                ws.write(row, 5, record['late_days'])
                ws.write(row, 6, record['leave_days'])
                
        elif report_type == 'leave':
            ws = workbook.add_worksheet('Leave Statistics')
            headers = ['Type', 'Count', 'Average Duration']
            for col, header in enumerate(headers):
                ws.write(0, col, header)
            
            for row, stat in enumerate(data['leave_type_stats'], 1):
                ws.write(row, 0, stat['leave_type'])
                ws.write(row, 1, stat['count'])
                ws.write(row, 2, round(stat['avg_duration'], 2) if stat['avg_duration'] else 0)
                
        elif report_type == 'holiday':
            ws = workbook.add_worksheet('Holidays')
            headers = ['Date', 'Name', 'Description', 'Type']
            for col, header in enumerate(headers):
                ws.write(0, col, header)
            
            for row, holiday in enumerate(data['holidays'], 1):
                ws.write(row, 0, holiday['date'])
                ws.write(row, 1, holiday['name'])
                ws.write(row, 2, holiday['description'])
                ws.write(row, 3, holiday['type'])
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{report_type}_report.xlsx"'
        return response