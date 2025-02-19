from typing import Dict, Any, Optional
from datetime import datetime
import tempfile
from pathlib import Path

from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

class PDFReportService:
    """Service for generating PDF reports from attendance data"""
    
    @classmethod
    def generate_attendance_report_pdf(cls, data: Dict[str, Any], template_name: str = 'attendance/pdf/attendance_report.html') -> bytes:
        """
        Generate PDF report for attendance data
        
        Args:
            data: Dictionary containing report data
            template_name: Name of the template to use for PDF generation
            
        Returns:
            PDF file content as bytes
        """
        # Prepare the HTML content
        html_string = render_to_string(template_name, {
            'data': data,
            'generated_at': datetime.now(),
            'report_type': 'Attendance Report'
        })
        
        # Set up fonts
        font_config = FontConfiguration()
        
        # Get CSS for PDF
        css_string = cls._get_report_css()
        
        # Create PDF
        html = HTML(string=html_string)
        css = CSS(string=css_string, font_config=font_config)
        
        # Use temp file to avoid memory issues with large reports
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            html.write_pdf(
                target=tmp_file.name,
                stylesheets=[css],
                font_config=font_config,
                presentational_hints=True
            )
            
            # Read the generated PDF
            with open(tmp_file.name, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
                
        # Clean up temp file
        Path(tmp_file.name).unlink()
        
        return pdf_content
    
    @classmethod
    def generate_leave_report_pdf(cls, data: Dict[str, Any], template_name: str = 'attendance/pdf/leave_report.html') -> bytes:
        """Generate PDF report for leave data"""
        html_string = render_to_string(template_name, {
            'data': data,
            'generated_at': datetime.now(),
            'report_type': 'Leave Report'
        })
        
        font_config = FontConfiguration()
        css_string = cls._get_report_css()
        
        html = HTML(string=html_string)
        css = CSS(string=css_string, font_config=font_config)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            html.write_pdf(
                target=tmp_file.name,
                stylesheets=[css],
                font_config=font_config,
                presentational_hints=True
            )
            
            with open(tmp_file.name, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
                
        Path(tmp_file.name).unlink()
        
        return pdf_content
    
    @classmethod
    def generate_holiday_report_pdf(cls, data: Dict[str, Any], template_name: str = 'attendance/pdf/holiday_report.html') -> bytes:
        """Generate PDF report for holiday data"""
        html_string = render_to_string(template_name, {
            'data': data,
            'generated_at': datetime.now(),
            'report_type': 'Holiday Report'
        })
        
        font_config = FontConfiguration()
        css_string = cls._get_report_css()
        
        html = HTML(string=html_string)
        css = CSS(string=css_string, font_config=font_config)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            html.write_pdf(
                target=tmp_file.name,
                stylesheets=[css],
                font_config=font_config,
                presentational_hints=True
            )
            
            with open(tmp_file.name, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
                
        Path(tmp_file.name).unlink()
        
        return pdf_content
    
    @staticmethod
    def _get_report_css() -> str:
        """Get CSS styles for PDF reports"""
        return """
            @page {
                size: A4;
                margin: 2.5cm 1.5cm;
                @top-center {
                    content: string(title);
                }
                @bottom-right {
                    content: "Page " counter(page) " of " counter(pages);
                }
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                line-height: 1.4;
                font-size: 11pt;
                color: #333;
            }
            
            .report-header {
                text-align: center;
                margin-bottom: 2em;
                string-set: title content();
            }
            
            .report-title {
                font-size: 24pt;
                font-weight: bold;
                margin-bottom: 0.5em;
            }
            
            .report-subtitle {
                font-size: 14pt;
                color: #666;
            }
            
            .summary-cards {
                display: flex;
                justify-content: space-between;
                margin: 2em 0;
            }
            
            .summary-card {
                padding: 1em;
                border: 1px solid #ddd;
                border-radius: 4px;
                width: 23%;
            }
            
            .summary-card h3 {
                margin: 0;
                color: #666;
                font-size: 12pt;
            }
            
            .summary-card .value {
                font-size: 20pt;
                font-weight: bold;
                margin: 0.5em 0;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 1em 0;
            }
            
            th, td {
                padding: 0.5em;
                border: 1px solid #ddd;
                text-align: left;
            }
            
            th {
                background-color: #f5f5f5;
                font-weight: bold;
            }
            
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            
            .chart-container {
                margin: 2em 0;
                page-break-inside: avoid;
            }
            
            .footer {
                margin-top: 2em;
                font-size: 9pt;
                color: #666;
                text-align: center;
            }
        """