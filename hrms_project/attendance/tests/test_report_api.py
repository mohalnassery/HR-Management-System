from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import datetime, date, timedelta

from attendance.models import (
    AttendanceLog, Leave, Holiday, LeaveType,
    Department, Employee
)

User = get_user_model()

class ReportAPITest(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
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
        
        # Create test dates
        self.today = timezone.now().date()
        self.start_date = self.today - timedelta(days=7)
        self.end_date = self.today
        
        # Create attendance logs
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
        
        # Create leave record
        Leave.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=self.start_date,
            end_date=self.start_date + timedelta(days=1),
            status='approved'
        )
        
        # Create holiday
        Holiday.objects.create(
            date=self.start_date + timedelta(days=2),
            name="Test Holiday",
            description="Test Holiday Description",
            is_active=True
        )

    def test_attendance_report_endpoint(self):
        """Test attendance report generation endpoint"""
        url = reverse('report-attendance')
        params = {
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d')
        }
        
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('summary', data)
        self.assertIn('trend_data', data)
        self.assertIn('department_stats', data)
        self.assertIn('employee_records', data)

    def test_leave_report_endpoint(self):
        """Test leave report generation endpoint"""
        url = reverse('report-leave')
        params = {
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d')
        }
        
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('total_leaves', data)
        self.assertIn('leave_type_stats', data)

    def test_holiday_report_endpoint(self):
        """Test holiday report generation endpoint"""
        url = reverse('report-holiday')
        params = {
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d')
        }
        
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('total_holidays', data)
        self.assertIn('holidays', data)

    def test_export_endpoint(self):
        """Test report export endpoint"""
        url = reverse('report-export')
        
        # Test CSV export
        params = {
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'type': 'attendance',
            'format': 'csv'
        }
        
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        
        # Test Excel export
        params['format'] = 'excel'
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Test PDF export
        params['format'] = 'pdf'
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_invalid_date_range(self):
        """Test report generation with invalid date range"""
        url = reverse('report-attendance')
        params = {
            'start_date': self.end_date.strftime('%Y-%m-%d'),
            'end_date': self.start_date.strftime('%Y-%m-%d')  # End date before start date
        }
        
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_parameters(self):
        """Test report generation with various filters"""
        url = reverse('report-attendance')
        params = {
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'departments': [self.department.id],
            'status': ['present', 'late']
        }
        
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(all(
            record['department'] == self.department.name
            for record in data['employee_records']
        ))

    def test_authentication_required(self):
        """Test that authentication is required for report endpoints"""
        self.client.logout()
        
        url = reverse('report-attendance')
        params = {
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d')
        }
        
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_export_with_invalid_format(self):
        """Test export endpoint with invalid format"""
        url = reverse('report-export')
        params = {
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'type': 'attendance',
            'format': 'invalid_format'
        }
        
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)