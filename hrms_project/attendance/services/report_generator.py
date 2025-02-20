from typing import Dict, Any, Optional, List
from datetime import datetime
import csv
import xlsxwriter
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .pdf_service import PDFReportService

class BaseReportGenerator:
    """Base class for report generation with common functionality"""
    
    def __init__(self, report_type: str):
        self.report_type = report_type
        self.exporters = {
            'csv': self._to_csv,
            'excel': self._to_excel,
            'pdf': self._to_pdf,
            'json': self._to_json
        }

    def generate(self, format: str, **params) -> Any:
        """
        Main entry point for report generation.
        
        Args:
            format: Output format (csv, excel, pdf, json)
            **params: Report parameters
            
        Returns:
            Generated report in requested format
        """
        data = self._gather_data(**params)
        exporter = self.exporters.get(format)
        if not exporter:
            raise ValueError(f"Unsupported format: {format}")
        return exporter(data)

    def _gather_data(self, **params) -> Dict:
        """
        Gather and process data for the report.
        To be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement _gather_data")

    def _to_json(self, data: Dict) -> Response:
        """Convert report data to JSON response"""
        return Response(data)

    def _to_pdf(self, data: Dict) -> HttpResponse:
        """Generate PDF report"""
        try:
            pdf_generators = {
                'attendance': PDFReportService.generate_attendance_report_pdf,
                'leave': PDFReportService.generate_leave_report_pdf,
                'holiday': PDFReportService.generate_holiday_report_pdf
            }
            
            generator = pdf_generators.get(self.report_type)
            if not generator:
                raise ValueError(f"PDF generation not supported for {self.report_type}")
            
            pdf_content = generator(data)
            filename = f"{self.report_type}_report_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            raise ValidationError(f"Error generating PDF: {str(e)}")

    def _to_csv(self, data: Dict) -> HttpResponse:
        """Generate CSV report"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{self.report_type}_report.csv"'
        writer = csv.writer(response)
        self._write_csv(writer, data)
        return response

    def _to_excel(self, data: Dict) -> HttpResponse:
        """Generate Excel report"""
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{self.report_type}_report.xlsx"'
        
        workbook = xlsxwriter.Workbook(response)
        self._write_excel(workbook, data)
        workbook.close()
        return response

    def _write_csv(self, writer: csv.writer, data: Dict):
        """Write data to CSV format. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _write_csv")

    def _write_excel(self, workbook: 'xlsxwriter.Workbook', data: Dict):
        """Write data to Excel format. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _write_excel")

class AttendanceReportGenerator(BaseReportGenerator):
    """Generator for attendance reports"""
    
    def __init__(self):
        super().__init__('attendance')

    def _gather_data(self, **params) -> Dict:
        from .report_service import ReportService
        return ReportService.get_attendance_report(**params)

    def _write_csv(self, writer: csv.writer, data: Dict):
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

    def _write_excel(self, workbook: 'xlsxwriter.Workbook', data: Dict):
        # Summary worksheet
        ws = workbook.add_worksheet('Summary')
        ws.write('A1', 'Summary')
        ws.write('A2', 'Status')
        ws.write('B2', 'Count')
        row = 3
        for status, count in data['summary'].items():
            ws.write(f'A{row}', status.title())
            ws.write(f'B{row}', count)
            row += 1
        
        # Employee records worksheet
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

class LeaveReportGenerator(BaseReportGenerator):
    """Generator for leave reports"""
    
    def __init__(self):
        super().__init__('leave')

    def _gather_data(self, **params) -> Dict:
        from .report_service import ReportService
        return ReportService.get_leave_report(**params)

    def _write_csv(self, writer: csv.writer, data: Dict):
        writer.writerow(['Leave Type Statistics'])
        writer.writerow(['Type', 'Count', 'Average Duration'])
        for stat in data['leave_type_stats']:
            writer.writerow([
                stat['leave_type'],
                stat['count'],
                round(stat['avg_duration'], 2) if stat['avg_duration'] else 0
            ])

    def _write_excel(self, workbook: 'xlsxwriter.Workbook', data: Dict):
        ws = workbook.add_worksheet('Leave Statistics')
        headers = ['Type', 'Count', 'Average Duration']
        for col, header in enumerate(headers):
            ws.write(0, col, header)
        
        for row, stat in enumerate(data['leave_type_stats'], 1):
            ws.write(row, 0, stat['leave_type'])
            ws.write(row, 1, stat['count'])
            ws.write(row, 2, round(stat['avg_duration'], 2) if stat['avg_duration'] else 0)

class HolidayReportGenerator(BaseReportGenerator):
    """Generator for holiday reports"""
    
    def __init__(self):
        super().__init__('holiday')

    def _gather_data(self, **params) -> Dict:
        from .report_service import ReportService
        return ReportService.get_holiday_report(**params)

    def _write_csv(self, writer: csv.writer, data: Dict):
        writer.writerow(['Date', 'Name', 'Description', 'Type'])
        for holiday in data['holidays']:
            writer.writerow([
                holiday['date'],
                holiday['name'],
                holiday['description'],
                holiday['type']
            ])

    def _write_excel(self, workbook: 'xlsxwriter.Workbook', data: Dict):
        ws = workbook.add_worksheet('Holidays')
        headers = ['Date', 'Name', 'Description', 'Type']
        for col, header in enumerate(headers):
            ws.write(0, col, header)
        
        for row, holiday in enumerate(data['holidays'], 1):
            ws.write(row, 0, holiday['date'])
            ws.write(row, 1, holiday['name'])
            ws.write(row, 2, holiday['description'])
            ws.write(row, 3, holiday['type'])

class ReportGeneratorFactory:
    """Factory for creating report generators"""
    
    GENERATORS = {
        'attendance': AttendanceReportGenerator,
        'leave': LeaveReportGenerator,
        'holiday': HolidayReportGenerator
    }
    
    @classmethod
    def create(cls, report_type: str) -> BaseReportGenerator:
        """Create appropriate report generator instance"""
        generator_class = cls.GENERATORS.get(report_type)
        if not generator_class:
            raise ValueError(f"Unknown report type: {report_type}")
        return generator_class()
