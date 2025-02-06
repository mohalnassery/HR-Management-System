import logging
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Count, Avg, Q, Sum, F, ExpressionWrapper, fields
from django.db.models.functions import ExtractHour, ExtractMinute
from datetime import datetime, timedelta
from attendance.models import AttendanceLog, Leave, LeaveType, LeaveBalance
from employees.models import Employee, Department
import os
import csv
from io import StringIO
import json

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate attendance and leave reports for specified period'

    def add_arguments(self, parser):
        parser.add_argument(
            '--report-type',
            type=str,
            choices=['daily', 'weekly', 'monthly', 'custom'],
            default='monthly',
            help='Type of report to generate'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date for custom report (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date for custom report (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--department',
            type=int,
            help='Department ID to filter report'
        )
        parser.add_argument(
            '--employee',
            type=int,
            help='Employee ID to generate individual report'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['html', 'csv', 'json'],
            default='html',
            help='Output format for the report'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            help='Directory to save report files'
        )

    def handle(self, *args, **options):
        report_type = options['report_type']
        format_type = options['format']
        output_dir = options.get('output_dir') or 'reports'

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Calculate date range
        end_date = timezone.now().date()
        if report_type == 'daily':
            start_date = end_date
        elif report_type == 'weekly':
            start_date = end_date - timedelta(days=7)
        elif report_type == 'monthly':
            start_date = end_date.replace(day=1)
        else:  # custom
            try:
                start_date = datetime.strptime(options['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(options['end_date'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                self.stderr.write('Invalid date format. Use YYYY-MM-DD')
                return

        # Get filters
        department_id = options.get('department')
        employee_id = options.get('employee')

        try:
            # Generate reports based on scope
            if employee_id:
                self._generate_employee_report(
                    employee_id, start_date, end_date, format_type, output_dir
                )
            elif department_id:
                self._generate_department_report(
                    department_id, start_date, end_date, format_type, output_dir
                )
            else:
                self._generate_organization_report(
                    start_date, end_date, format_type, output_dir
                )

            self.stdout.write(self.style.SUCCESS(
                f'Successfully generated {report_type} report(s) in {format_type} format'
            ))

        except Exception as e:
            logger.error(f'Error generating report: {str(e)}')
            self.stderr.write(f'Error generating report: {str(e)}')
            raise

    def _generate_employee_report(self, employee_id, start_date, end_date, format_type, output_dir):
        """Generate detailed report for a single employee"""
        employee = Employee.objects.get(id=employee_id)
        
        # Get attendance logs
        attendance_logs = AttendanceLog.objects.filter(
            employee=employee,
            date__range=[start_date, end_date]
        ).order_by('date')

        # Calculate attendance statistics
        total_days = (end_date - start_date).days + 1
        present_days = attendance_logs.filter(first_in_time__isnull=False).count()
        absent_days = attendance_logs.filter(first_in_time__isnull=True).count()
        late_days = attendance_logs.filter(is_late=True).count()

        # Calculate average arrival and departure times
        avg_arrival = attendance_logs.exclude(
            first_in_time__isnull=True
        ).annotate(
            hour=ExtractHour('first_in_time'),
            minute=ExtractMinute('first_in_time')
        ).aggregate(
            avg_hour=Avg('hour'),
            avg_minute=Avg('minute')
        )

        # Get leave information
        leaves = Leave.objects.filter(
            employee=employee,
            start_date__lte=end_date,
            end_date__gte=start_date
        ).select_related('leave_type')

        # Get leave balances
        leave_balances = LeaveBalance.objects.filter(
            employee=employee,
            is_active=True
        ).select_related('leave_type')

        report_data = {
            'employee': employee,
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'total_days': total_days
            },
            'attendance': {
                'present_days': present_days,
                'absent_days': absent_days,
                'late_days': late_days,
                'attendance_rate': (present_days / total_days * 100) if total_days > 0 else 0,
                'avg_arrival_time': (
                    f"{int(avg_arrival['avg_hour'] or 0):02d}:"
                    f"{int(avg_arrival['avg_minute'] or 0):02d}"
                ),
                'logs': attendance_logs
            },
            'leaves': leaves,
            'leave_balances': leave_balances,
            'generated_at': timezone.now()
        }

        # Generate report in specified format
        filename = f"employee_report_{employee.employee_number}_{start_date}_{end_date}"
        self._save_report(report_data, format_type, filename, output_dir, 'employee_report.html')

    def _generate_department_report(self, department_id, start_date, end_date, format_type, output_dir):
        """Generate summary report for a department"""
        department = Department.objects.get(id=department_id)
        employees = Employee.objects.filter(department=department, is_active=True)

        # Calculate department statistics
        total_days = (end_date - start_date).days + 1
        attendance_stats = AttendanceLog.objects.filter(
            employee__department=department,
            date__range=[start_date, end_date]
        ).aggregate(
            total_present=Count('id', filter=Q(first_in_time__isnull=False)),
            total_absent=Count('id', filter=Q(first_in_time__isnull=True)),
            total_late=Count('id', filter=Q(is_late=True))
        )

        # Calculate leave statistics
        leave_stats = Leave.objects.filter(
            employee__department=department,
            start_date__lte=end_date,
            end_date__gte=start_date,
            status='approved'
        ).values('leave_type__name').annotate(
            total_days=Count('id'),
            total_employees=Count('employee', distinct=True)
        )

        report_data = {
            'department': department,
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'total_days': total_days
            },
            'statistics': {
                'total_employees': employees.count(),
                'present_rate': (attendance_stats['total_present'] / (total_days * employees.count()) * 100) if employees.count() > 0 else 0,
                'absent_rate': (attendance_stats['total_absent'] / (total_days * employees.count()) * 100) if employees.count() > 0 else 0,
                'late_rate': (attendance_stats['total_late'] / attendance_stats['total_present'] * 100) if attendance_stats['total_present'] > 0 else 0,
            },
            'attendance': attendance_stats,
            'leave_stats': leave_stats,
            'employees': employees,
            'generated_at': timezone.now()
        }

        # Generate report in specified format
        filename = f"department_report_{department.code}_{start_date}_{end_date}"
        self._save_report(report_data, format_type, filename, output_dir, 'department_report.html')

    def _generate_organization_report(self, start_date, end_date, format_type, output_dir):
        """Generate overall organization attendance and leave report"""
        departments = Department.objects.all()
        total_days = (end_date - start_date).days + 1

        # Overall statistics
        org_stats = AttendanceLog.objects.filter(
            date__range=[start_date, end_date]
        ).aggregate(
            total_present=Count('id', filter=Q(first_in_time__isnull=False)),
            total_absent=Count('id', filter=Q(first_in_time__isnull=True)),
            total_late=Count('id', filter=Q(is_late=True))
        )

        # Department-wise statistics
        dept_stats = []
        for dept in departments:
            stats = AttendanceLog.objects.filter(
                employee__department=dept,
                date__range=[start_date, end_date]
            ).aggregate(
                present=Count('id', filter=Q(first_in_time__isnull=False)),
                absent=Count('id', filter=Q(first_in_time__isnull=True)),
                late=Count('id', filter=Q(is_late=True))
            )
            dept_stats.append({
                'department': dept,
                'stats': stats
            })

        # Leave type statistics
        leave_stats = Leave.objects.filter(
            start_date__lte=end_date,
            end_date__gte=start_date,
            status='approved'
        ).values('leave_type__name').annotate(
            total_days=Count('id'),
            total_employees=Count('employee', distinct=True)
        )

        report_data = {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'total_days': total_days
            },
            'organization': {
                'total_departments': departments.count(),
                'total_employees': Employee.objects.filter(is_active=True).count(),
                'stats': org_stats
            },
            'department_stats': dept_stats,
            'leave_stats': leave_stats,
            'generated_at': timezone.now()
        }

        # Generate report in specified format
        filename = f"organization_report_{start_date}_{end_date}"
        self._save_report(report_data, format_type, filename, output_dir, 'organization_report.html')

    def _save_report(self, data, format_type, filename, output_dir, template_name):
        """Save report in specified format"""
        if format_type == 'html':
            content = render_to_string(f'attendance/reports/{template_name}', data)
            filepath = os.path.join(output_dir, f'{filename}.html')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

        elif format_type == 'csv':
            filepath = os.path.join(output_dir, f'{filename}.csv')
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                self._write_csv_data(writer, data)

        elif format_type == 'json':
            filepath = os.path.join(output_dir, f'{filename}.json')
            with open(filepath, 'w', encoding='utf-8') as f:
                # Convert datetime objects to string format
                json.dump(self._prepare_json_data(data), f, indent=2, default=str)

    def _write_csv_data(self, writer, data):
        """Convert report data to CSV format"""
        # Write header
        writer.writerow(['Report Generated:', data['generated_at'].strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['Period:', f"{data['period']['start_date']} to {data['period']['end_date']}"])
        writer.writerow([])

        # Write statistics
        if 'statistics' in data:
            writer.writerow(['Statistics'])
            for key, value in data['statistics'].items():
                writer.writerow([key.replace('_', ' ').title(), f"{value:.2f}%"])
            writer.writerow([])

        # Write attendance data if available
        if 'attendance' in data and isinstance(data['attendance'], dict):
            writer.writerow(['Attendance Summary'])
            for key, value in data['attendance'].items():
                writer.writerow([key.replace('_', ' ').title(), value])

    def _prepare_json_data(self, data):
        """Prepare data for JSON serialization"""
        # Convert model instances to dictionaries
        if isinstance(data, dict):
            return {k: self._prepare_json_data(v) for k, v in data.items()}
        elif hasattr(data, '_meta'):  # Django model instance
            return {
                field.name: getattr(data, field.name)
                for field in data._meta.fields
            }
        elif isinstance(data, (list, tuple)):
            return [self._prepare_json_data(item) for item in data]
        return data
