from django.test import TestCase
from django.utils import timezone
from datetime import datetime, date, timedelta
from django.core.files.base import ContentFile

from attendance.models import (
    AttendanceLog, Leave, Holiday, LeaveType,
    Department, Employee
)
from attendance.services.report_service import ReportService
from attendance.services.pdf_service import PDFReportService

class ReportServicesTest(TestCase):
    def setUp(self):
        # Create test data
        self.department = Department.objects.create(name="Test Department")
        self.employee = Employee.objects.create(
            first_name="John",
            last_name="Doe",
            employee_number="EMP001",
            department=self.department
        )
        
        self.leave_type = LeaveType.objects.create(
            name="Annual Leave",
            days_per_year=21
        )
        
        # Create attendance logs
        self.today = timezone.now().date()
        self.start_date = self.today - timedelta(days=7)
        self.end_date = self.today
        
        # Create attendance logs for the past week
        for i in range(8):
            date = self.today - timedelta(days=i)
            AttendanceLog.objects.create(
                employee=self.employee,
                date=date,
                first_in_time=timezone.datetime.strptime('09:00', '%H:%M').time(),
                last_out_time=timezone.datetime.strptime('17:00', '%H:%M').time(),
                is_present=True,
                is_late=False if i % 2 == 0 else True
            )
        
        # Create a leave record
        Leave.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=self.start_date,
            end_date=self.start_date + timedelta(days=1),
            status='approved'
        )
        
        # Create a holiday
        Holiday.objects.create(
            date=self.start_date + timedelta(days=2),
            name="Test Holiday",
            description="Test Holiday Description",
            is_active=True
        )

    def test_attendance_report_generation(self):
        """Test attendance report generation"""
        report_data = ReportService.get_attendance_report(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        # Verify report structure and data
        self.assertIn('summary', report_data)
        self.assertIn('trend_data', report_data)
        self.assertIn('department_stats', report_data)
        self.assertIn('employee_records', report_data)
        
        # Verify summary counts
        summary = report_data['summary']
        self.assertIn('present', summary)
        self.assertIn('absent', summary)
        self.assertIn('late', summary)
        self.assertIn('leave', summary)
        
        # Verify employee records
        self.assertEqual(len(report_data['employee_records']), 1)
        record = report_data['employee_records'][0]
        self.assertEqual(record['name'], "John Doe")

    def test_leave_report_generation(self):
        """Test leave report generation"""
        report_data = ReportService.get_leave_report(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        # Verify leave report structure
        self.assertIn('total_leaves', report_data)
        self.assertIn('approved_leaves', report_data)
        self.assertIn('pending_leaves', report_data)
        self.assertIn('leave_type_stats', report_data)
        
        # Verify leave counts
        self.assertEqual(report_data['total_leaves'], 1)
        self.assertEqual(report_data['approved_leaves'], 1)

    def test_holiday_report_generation(self):
        """Test holiday report generation"""
        report_data = ReportService.get_holiday_report(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        # Verify holiday report structure
        self.assertIn('total_holidays', report_data)
        self.assertIn('holidays', report_data)
        
        # Verify holiday data
        self.assertEqual(report_data['total_holidays'], 1)
        self.assertEqual(len(report_data['holidays']), 1)
        self.assertEqual(report_data['holidays'][0]['name'], "Test Holiday")

    def test_pdf_generation(self):
        """Test PDF report generation"""
        # Generate attendance report data
        report_data = ReportService.get_attendance_report(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        # Test attendance report PDF
        pdf_content = PDFReportService.generate_attendance_report_pdf(report_data)
        self.assertIsInstance(pdf_content, bytes)
        self.assertTrue(pdf_content.startswith(b'%PDF'))
        
        # Test leave report PDF
        leave_data = ReportService.get_leave_report(
            start_date=self.start_date,
            end_date=self.end_date
        )
        pdf_content = PDFReportService.generate_leave_report_pdf(leave_data)
        self.assertIsInstance(pdf_content, bytes)
        self.assertTrue(pdf_content.startswith(b'%PDF'))
        
        # Test holiday report PDF
        holiday_data = ReportService.get_holiday_report(
            start_date=self.start_date,
            end_date=self.end_date
        )
        pdf_content = PDFReportService.generate_holiday_report_pdf(holiday_data)
        self.assertIsInstance(pdf_content, bytes)
        self.assertTrue(pdf_content.startswith(b'%PDF'))

    def test_report_with_filters(self):
        """Test report generation with filters"""
        report_data = ReportService.get_attendance_report(
            start_date=self.start_date,
            end_date=self.end_date,
            departments=[self.department.id],
            status=['present', 'late']
        )
        
        # Verify filtered data
        self.assertTrue(all(
            record['department'] == self.department.name
            for record in report_data['employee_records']
        ))
        
        # Test with employee filter
        report_data = ReportService.get_attendance_report(
            start_date=self.start_date,
            end_date=self.end_date,
            employees=[self.employee.id]
        )
        
        self.assertEqual(len(report_data['employee_records']), 1)
        self.assertEqual(
            report_data['employee_records'][0]['id'],
            self.employee.id
        )

    def test_export_formats(self):
        """Test different export formats"""
        report_data = ReportService.get_attendance_report(
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        # Test PDF format
        pdf_content = PDFReportService.generate_attendance_report_pdf(report_data)
        self.assertTrue(pdf_content.startswith(b'%PDF'))
        
        # Save PDF to verify it's valid
        test_file = ContentFile(pdf_content)
        self.assertTrue(test_file.size > 0)