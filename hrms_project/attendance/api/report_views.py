from datetime import datetime
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.http import HttpResponse
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
import xlsxwriter
import csv

from ..models import AttendanceLog, Leave, Holiday
from ..serializers import AttendanceLogSerializer
from ..services.report_service import ReportService
from ..services.pdf_service import PDFReportService

class ReportViewSet(viewsets.ViewSet):
    """ViewSet for handling report generation and exports"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def attendance(self, request):
        """Generate attendance report"""
        try:
            # Get query parameters
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            departments = request.query_params.getlist('departments[]', [])
            employees = request.query_params.getlist('employees[]', [])
            status = request.query_params.getlist('status[]', []) or request.query_params.getlist('status', [])
            
            # Validate dates
            if not start_date or not end_date:
                raise ValidationError("Both start_date and end_date are required")
            
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                raise ValidationError("Invalid date format. Use YYYY-MM-DD")
            
            if start_date > end_date:
                raise ValidationError("Start date must be before end date")
            
            # Build parameters
            params = {
                'start_date': start_date,
                'end_date': end_date
            }
            
            # Add optional parameters
            if departments and departments[0]:
                params['departments'] = [int(d) for d in departments if d]
            if employees and employees[0]:
                params['employees'] = [int(e) for e in employees if e]
            if status and status[0]:
                params['status'] = status

            # Generate report
            data = ReportService.get_attendance_report(**params)
            return Response(data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": f"Unexpected error: {str(e)}"}, status=500)
    
    @action(detail=False, methods=['get'])
    def leave(self, request):
        """Generate leave report"""
        try:
            # Get query parameters
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            departments = request.query_params.getlist('departments[]', [])
            employees = request.query_params.getlist('employees[]', [])
            leave_types = request.query_params.getlist('leave_types[]', [])
            
            # Validate dates
            if not start_date or not end_date:
                raise ValidationError("Both start_date and end_date are required")
            
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                raise ValidationError("Invalid date format. Use YYYY-MM-DD")
            
            if start_date > end_date:
                raise ValidationError("Start date must be before end date")
            
            # Build parameters
            params = {
                'start_date': start_date,
                'end_date': end_date
            }
            
            # Add optional parameters
            if departments and departments[0]:
                params['departments'] = [int(d) for d in departments if d]
            if employees and employees[0]:
                params['employees'] = [int(e) for e in employees if e]
            if leave_types and leave_types[0]:
                params['leave_types'] = leave_types
            
            # Generate report
            data = ReportService.get_leave_report(**params)
            return Response(data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": f"Unexpected error: {str(e)}"}, status=500)
    
    @action(detail=False, methods=['get'])
    def holiday(self, request):
        """Generate holiday report"""
        try:
            # Get and validate dates
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            if not start_date or not end_date:
                raise ValidationError("Both start_date and end_date are required")
            
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                raise ValidationError("Invalid date format. Use YYYY-MM-DD")
            
            if start_date > end_date:
                raise ValidationError("Start date must be before end date")
            
            # Generate report
            data = ReportService.get_holiday_report(start_date, end_date)
            return Response(data)
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": f"Unexpected error: {str(e)}"}, status=500)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export report in specified format"""
        try:
            # Get export parameters
            report_type = request.query_params.get('type', 'attendance')
            export_format = request.query_params.get('format', 'csv')
            
            # Build report parameters similar to above methods
            params = {}
            
            # Get and validate dates
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            if not start_date or not end_date:
                raise ValidationError("Both start_date and end_date are required")
            
            try:
                params['start_date'] = datetime.strptime(start_date, '%Y-%m-%d')
                params['end_date'] = datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                raise ValidationError("Invalid date format. Use YYYY-MM-DD")
            
            # Add optional parameters based on report type
            if report_type in ['attendance', 'leave']:
                departments = request.query_params.getlist('departments[]', [])
                employees = request.query_params.getlist('employees[]', [])
                
                if departments and departments[0]:
                    params['departments'] = [int(d) for d in departments if d]
                if employees and employees[0]:
                    params['employees'] = [int(e) for e in employees if e]
                
                if report_type == 'attendance':
                    status = request.query_params.getlist('status[]', []) or request.query_params.getlist('status', [])
                    if status and status[0]:
                        params['status'] = status
                elif report_type == 'leave':
                    leave_types = request.query_params.getlist('leave_types[]', [])
                    if leave_types and leave_types[0]:
                        params['leave_types'] = leave_types
            
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
            return Response({"error": f"Unexpected error: {str(e)}"}, status=500)
    
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
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
        
        writer = csv.writer(response)
        
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
        
        return response
    
    def _export_excel(self, data: dict, report_type: str) -> HttpResponse:
        """Export report as Excel"""
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{report_type}_report.xlsx"'
        
        workbook = xlsxwriter.Workbook(response)
        
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
        return response
