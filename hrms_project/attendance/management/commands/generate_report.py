import logging
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Count, Avg, Q, Sum, F, ExpressionWrapper, fields
from django.db.models.functions import ExtractHour, ExtractMinute
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, Tuple, List, Union
from dataclasses import dataclass
from django.core.serializers.json import DjangoJSONEncoder
from attendance.models import AttendanceLog, Leave, LeaveType, LeaveBalance
from employees.models import Employee, Department
import os
import csv
from io import StringIO
import json

logger = logging.getLogger(__name__)

@dataclass
class DateRange:
    """Data class to hold date range information"""
    start_date: date
    end_date: date
    total_days: int

    @property
    def as_dict(self) -> Dict[str, Any]:
        return {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'total_days': self.total_days
        }

class ReportGenerator:
    """Base class for report generation functionality"""
    
    def __init__(self, start_date: date, end_date: date):
        self.date_range = DateRange(
            start_date=start_date,
            end_date=end_date,
            total_days=(end_date - start_date).days + 1
        )
        self.generated_at = timezone.now()

    def get_attendance_stats(self, queryset: Any) -> Dict[str, int]:
        """Calculate attendance statistics for a queryset"""
        return queryset.aggregate(
            total_present=Count('id', filter=Q(first_in_time__isnull=False)),
            total_absent=Count('id', filter=Q(first_in_time__isnull=True)),
            total_late=Count('id', filter=Q(is_late=True))
        )

    def get_leave_stats(self, queryset: Any) -> List[Dict[str, Any]]:
        """Calculate leave statistics for a queryset"""
        return list(queryset.values('leave_type__name').annotate(
            total_days=Count('id'),
            total_employees=Count('employee', distinct=True)
        ))

    def prepare_base_data(self) -> Dict[str, Any]:
        """Prepare common report data"""
        return {
            'period': self.date_range.as_dict,
            'generated_at': self.generated_at
        }

class ReportExporter:
    """Handles report export functionality"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save_report(
        self,
        data: Dict[str, Any],
        format_type: str,
        filename: str,
        template_name: Optional[str] = None
    ) -> None:
        """
        Save report in specified format using appropriate handler
        """
        handlers = {
            'html': self._save_html,
            'csv': self._save_csv,
            'json': self._save_json
        }
        
        handler = handlers.get(format_type)
        if not handler:
            raise ValueError(f"Unsupported format: {format_type}")
        
        filepath = os.path.join(self.output_dir, f'{filename}.{format_type}')
        handler(data, filepath, template_name)

    def _save_html(self, data: Dict[str, Any], filepath: str, template_name: str) -> None:
        """Save report as HTML"""
        content = render_to_string(f'attendance/reports/{template_name}', data)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    def _save_csv(self, data: Dict[str, Any], filepath: str, _: str) -> None:
        """Save report as CSV"""
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            self._write_csv_data(writer, data)

    def _save_json(self, data: Dict[str, Any], filepath: str, _: str) -> None:
        """Save report as JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(
                self._prepare_json_data(data),
                f,
                indent=2,
                cls=DjangoJSONEncoder
            )

    def _write_csv_data(self, writer: csv.writer, data: Dict[str, Any]) -> None:
        """Write report data in CSV format"""
        # Write header
        writer.writerow(['Report Generated:', data['generated_at'].strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['Period:', f"{data['period']['start_date']} to {data['period']['end_date']}"])
        writer.writerow([])

        # Write statistics
        if 'statistics' in data:
            writer.writerow(['Statistics'])
            for key, value in data['statistics'].items():
                if isinstance(value, (int, float)):
                    value = f"{value:.2f}%"
                writer.writerow([key.replace('_', ' ').title(), value])
            writer.writerow([])

        # Write attendance data
        if 'attendance' in data and isinstance(data['attendance'], dict):
            writer.writerow(['Attendance Summary'])
            for key, value in data['attendance'].items():
                if key != 'logs':  # Skip detailed logs
                    writer.writerow([key.replace('_', ' ').title(), value])

    def _prepare_json_data(self, data: Any) -> Any:
        """Prepare data for JSON serialization"""
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

    def calculate_date_range(
        self,
        report_type: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> DateRange:
        """Calculate start and end dates based on report type"""
        end = timezone.now().date()
        
        if report_type == 'daily':
            start = end
        elif report_type == 'weekly':
            start = end - timedelta(days=7)
        elif report_type == 'monthly':
            start = end.replace(day=1)
        else:  # custom
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                raise ValueError('Invalid date format. Use YYYY-MM-DD')
        
        return DateRange(start, end, (end - start).days + 1)

    def handle(self, *args, **options):
        try:
            # Calculate date range
            date_range = self.calculate_date_range(
                options['report_type'],
                options.get('start_date'),
                options.get('end_date')
            )

            # Initialize report exporter
            exporter = ReportExporter(options.get('output_dir', 'reports'))

            # Generate appropriate report
            if options.get('employee'):
                self._generate_employee_report(
                    options['employee'],
                    date_range,
                    options['format'],
                    exporter
                )
            elif options.get('department'):
                self._generate_department_report(
                    options['department'],
                    date_range,
                    options['format'],
                    exporter
                )
            else:
                self._generate_organization_report(
                    date_range,
                    options['format'],
                    exporter
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully generated {options["report_type"]} report(s) '
                    f'in {options["format"]} format'
                )
            )

        except Exception as e:
            logger.error(f'Error generating report: {str(e)}')
            self.stderr.write(f'Error generating report: {str(e)}')
            raise

    def _generate_employee_report(
        self,
        employee_id: int,
        date_range: DateRange,
        format_type: str,
        exporter: ReportExporter
    ) -> None:
        """Generate detailed report for a single employee"""
        employee = Employee.objects.get(id=employee_id)
        
        # Get attendance logs
        attendance_logs = AttendanceLog.objects.filter(
            employee=employee,
            date__range=[date_range.start_date, date_range.end_date]
        ).order_by('date')

        # Calculate attendance statistics
        present_days = attendance_logs.filter(first_in_time__isnull=False).count()
        absent_days = attendance_logs.filter(first_in_time__isnull=True).count()
        late_days = attendance_logs.filter(is_late=True).count()

        # Calculate average arrival time
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
            start_date__lte=date_range.end_date,
            end_date__gte=date_range.start_date
        ).select_related('leave_type')

        # Get leave balances
        leave_balances = LeaveBalance.objects.filter(
            employee=employee,
            is_active=True
        ).select_related('leave_type')

        report_data = {
            'employee': employee,
            'period': date_range.as_dict,
            'attendance': {
                'present_days': present_days,
                'absent_days': absent_days,
                'late_days': late_days,
                'attendance_rate': (present_days / date_range.total_days * 100) if date_range.total_days > 0 else 0,
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

        filename = f"employee_report_{employee.employee_number}_{date_range.start_date}_{date_range.end_date}"
        exporter.save_report(report_data, format_type, filename, 'employee_report.html')

    def _generate_department_report(
        self,
        department_id: int,
        date_range: DateRange,
        format_type: str,
        exporter: ReportExporter
    ) -> None:
        """Generate summary report for a department"""
        department = Department.objects.get(id=department_id)
        employees = Employee.objects.filter(department=department, is_active=True)

        # Calculate department statistics
        attendance_stats = AttendanceLog.objects.filter(
            employee__department=department,
            date__range=[date_range.start_date, date_range.end_date]
        ).aggregate(
            total_present=Count('id', filter=Q(first_in_time__isnull=False)),
            total_absent=Count('id', filter=Q(first_in_time__isnull=True)),
            total_late=Count('id', filter=Q(is_late=True))
        )

        # Calculate leave statistics
        leave_stats = Leave.objects.filter(
            employee__department=department,
            start_date__lte=date_range.end_date,
            end_date__gte=date_range.start_date,
            status='approved'
        ).values('leave_type__name').annotate(
            total_days=Count('id'),
            total_employees=Count('employee', distinct=True)
        )

        employee_count = employees.count()
        report_data = {
            'department': department,
            'period': date_range.as_dict,
            'statistics': {
                'total_employees': employee_count,
                'present_rate': (attendance_stats['total_present'] / (date_range.total_days * employee_count) * 100) if employee_count > 0 else 0,
                'absent_rate': (attendance_stats['total_absent'] / (date_range.total_days * employee_count) * 100) if employee_count > 0 else 0,
                'late_rate': (attendance_stats['total_late'] / attendance_stats['total_present'] * 100) if attendance_stats['total_present'] > 0 else 0,
            },
            'attendance': attendance_stats,
            'leave_stats': leave_stats,
            'employees': employees,
            'generated_at': timezone.now()
        }

        filename = f"department_report_{department.code}_{date_range.start_date}_{date_range.end_date}"
        exporter.save_report(report_data, format_type, filename, 'department_report.html')

    def _generate_organization_report(
        self,
        date_range: DateRange,
        format_type: str,
        exporter: ReportExporter
    ) -> None:
        """Generate overall organization attendance and leave report"""
        departments = Department.objects.all()

        # Overall statistics
        org_stats = AttendanceLog.objects.filter(
            date__range=[date_range.start_date, date_range.end_date]
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
                date__range=[date_range.start_date, date_range.end_date]
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
            start_date__lte=date_range.end_date,
            end_date__gte=date_range.start_date,
            status='approved'
        ).values('leave_type__name').annotate(
            total_days=Count('id'),
            total_employees=Count('employee', distinct=True)
        )

        report_data = {
            'period': date_range.as_dict,
            'organization': {
                'total_departments': departments.count(),
                'total_employees': Employee.objects.filter(is_active=True).count(),
                'stats': org_stats
            },
            'department_stats': dept_stats,
            'leave_stats': leave_stats,
            'generated_at': timezone.now()
        }

        filename = f"organization_report_{date_range.start_date}_{date_range.end_date}"
        exporter.save_report(report_data, format_type, filename, 'organization_report.html')
