**Analysis of Files and Identification of Duplicates/Common Methods:**

**1. `hrms_project\attendance\admin.py`**

*   **`get_colored_display` function**: This function is used in `ShiftAdmin` and `AttendanceLogAdmin` to color-code display values in the admin interface. This is a utility function for formatting and is a good candidate for centralization.
*   **`EmployeeLinkedModelAdmin` class**: This is a base class for admin models related to employees, centralizing the `employee_link` method. This is already a good example of code centralization.
*   **`PeriodDisplayMixin` class**: This mixin centralizes the `period_display` method for models with start and end dates.  Another good example of centralization.

**2. `hrms_project\attendance\api\report_views.py`**

*   **`validate_report_params` decorator**: This decorator is used to validate report parameters across multiple report views. This is a good example of centralizing parameter validation logic.
*   **`ReportExporter` class**: This class centralizes report exporting functionality in different formats (CSV, Excel, PDF, JSON). This is excellent for code organization and reusability.  The individual `_export_*` and `_write_*_csv/excel` methods within this class are also well-organized for each format.
*   **`ReportViewSet` class**: This class centralizes report view logic and maps report types to service methods.  This is a good design pattern for managing different report types.

**3. `hrms_project\attendance\apps.py`**

*   **`_connect_model_signals` method**: This method centralizes the connection of signal handlers for different models. This is good for app configuration and maintainability.
*   **`_setup_celery_schedule` method**: This method centralizes Celery beat schedule setup. Good for app configuration.

**4. `hrms_project\attendance\cache.py`**

*   **`generate_cache_key` function**: Centralizes cache key generation, which is excellent for consistency.
*   **`CacheManager` class**: Provides a generic cache management class, promoting code reuse for different cache operations.
*   **`ShiftCache`, `RamadanCache`, `AttendanceMetricsCache` classes**: These classes are specialized cache managers, well-organized and leveraging the `CacheManager` class.
*   **`invalidate_employee_caches`, `invalidate_department_caches`, `warm_employee_caches` functions**: Centralized cache invalidation and warming functions. These are good for managing cache across the application.

**5. `hrms_project\attendance\forms.py`**

*   **`BaseForm` class**: Centralizes Bootstrap class addition to form widgets. Good for UI consistency.
*   **`BaseModelForm` class**: Combines `ModelForm` and `BaseForm`, good for consistent model forms.
*   **`DateRangeValidationMixin` class**: Centralizes date range validation logic.  Excellent for reusability across forms and serializers.

**6. `hrms_project\attendance\management\commands`**

*   **`CacheInvalidationService` class (in `cleanup_shifts.py`)**: Centralizes cache invalidation within management commands. Good for maintainability of cleanup tasks.
*   **`DataArchiver` class (in `cleanup_shifts.py`)**: Centralizes data archiving to CSV within management commands. Good for reusability in cleanup tasks.
*   **`ReportExporter` class (in `generate_report.py`)**: Similar to `ReportExporter` in `report_views.py`, this class handles report exporting within management commands. Although named the same and serving a similar purpose, these are separate classes in different contexts (views vs. management commands). While there's a conceptual duplication, they are used in distinct parts of the application (web requests vs. command-line tasks), so merging them might not be straightforward and might introduce unnecessary dependencies.  However, their functionalities are very similar, suggesting a potential for a shared base class or utility functions for export logic.
*   **`LeaveBalanceProcessor` and `LeaveBalanceFormatter` classes (in `recalculate_leave_balance.py`)**:  These classes organize the logic for recalculating and formatting leave balances in a management command.  Good for command-specific organization.
*   **`DateRange` dataclass (in `generate_report.py`)**:  A simple data class to hold date range info, which is good for clarity and organization within the report generation command.

**7. `hrms_project\attendance\migrations`**

*   Migrations are for database schema changes and data initialization, not directly related to code duplication in application logic.

**8. `hrms_project\attendance\models.py`**

*   **`clean` methods in models**:  `RamadanPeriod` and `ShiftAssignment` models have `clean` methods for model-level validation. This is good practice and not duplicated code.
*   **`Shift.get_default_shifts` method**: Class method to retrieve default shifts, which is a good way to encapsulate default data access.

**9. `hrms_project\attendance\schedules.py`**

*   **`BEAT_SCHEDULE` dictionary**: Centralized Celery Beat schedule configuration.  Good for task scheduling management.

**10. `hrms_project\attendance\serializers.py`**

*   **`EmployeeNameMixin`, `UserNameMixin`, `StatusDeterminationMixin` classes**: These mixins centralize common serialization logic for employee names, user names, and status determination. Excellent example of code reuse and organization in serializers.

**11. `hrms_project\attendance\services`**

*   The `services` package itself is a great example of centralization. It groups business logic related to different aspects of the application.
*   **`AttendanceStatusService` class**: Centralizes attendance status calculation logic, including handling shifts, Ramadan, and overrides. This is exactly what we are aiming for - centralizing the core business rules.
*   **`CacheInvalidationService` class**: Centralizes cache clearing logic.
*   **`LeaveBalanceService` class**: Centralizes leave balance calculation logic.
*   **`PDFReportService` class**: Centralizes PDF report generation, using `weasyprint`.
*   **`RamadanService` class**: Centralizes Ramadan period related logic.
*   **`ReportService` class**: Centralizes report data retrieval logic, including caching.
*   **`ShiftService` class**: Centralizes shift related logic.

**12. `hrms_project\attendance\services.py`**

*   This file seems to be a older version of `hrms_project\attendance\services\attendance_status_service.py` and other service files. It contains some duplicated logic that has been better organized into separate service classes. It should be reviewed and potentially removed if its functionalities are fully covered by the more organized `services` package.  If it contains any unique logic, that logic should be migrated into the appropriate service class within the `services` package.

**13. `hrms_project\attendance\signals.py`**

*   Signal handlers are well organized and handle model events. No significant duplication here.

**14. `hrms_project\attendance\static\attendance\css` and `js` folders**

*   These are for front-end assets and not directly related to backend code duplication.

**15. `hrms_project\attendance\templates` folder**

*   Templates are for UI presentation and not related to backend code duplication.

**16. `hrms_project\attendance\templatetags` folder**

*   Template tags are for presentation logic within templates and are well-organized. No duplication here.

**17. `hrms_project\attendance\tests` folder**

*   Tests are for verifying functionality and not related to code duplication in application logic.

**18. `hrms_project\attendance\urls.py`**

*   URLs are for routing and not related to code duplication in application logic.

**19. `hrms_project\attendance\utils\timing.py`**

*   This file contains utility functions for timing calculations, which is a great example of centralization.

**20. `hrms_project\attendance\utils.py`**

*   This file contains utility functions for processing attendance Excel files and generating attendance logs. It's a good place for these utility functions.


**Identified Areas for Potential Centralization/Refinement and Actions:**

1.  **`get_colored_display` function in `admin.py`**:
    *   **Action**: Move this utility function to a more general utility module, perhaps `hrms_project\attendance\utils.py` or create a new file `hrms_project\attendance\utils\admin_utils.py`.
    *   **Usage**: Import and use `get_colored_display` from the utility module in `ShiftAdmin` and `AttendanceLogAdmin`.

2.  **`ReportExporter` class in `api\report_views.py` and `management\commands\generate_report.py`**:
    *   **Issue**:  While conceptually similar, they are implemented separately.
    *   **Action**:  Consider creating a base `ReportExporter` class in a shared location (e.g., `hrms_project\attendance\services\report_exporter.py`) and have both `ReportExporter` in views and commands inherit from it or use it. Alternatively, create a set of utility functions for report export in `hrms_project\attendance\utils\report_utils.py` and use them in both contexts. This might involve moving the `_export_*` and `_write_*_csv/excel` methods to the utility functions or base class.
    *   **Usage**: Refactor `ReportViewSet` and `generate_report` command to use the centralized `ReportExporter` or utility functions.

3.  **`services.py` file**:
    *   **Issue**: This file seems outdated and contains logic that has been better organized into separate service classes in the `services` package.
    *   **Action**: Review `hrms_project\attendance\services.py` and migrate any unique and relevant logic to the appropriate service classes within the `services` package. After migration, if `services.py` becomes redundant, consider removing it to avoid confusion and maintain code clarity.

**Detailed Steps for Actionable Items:**

**1. Centralizing `get_colored_display`:**

*   **Create `hrms_project\attendance\utils\admin_utils.py`**:
    ```python
    from django.utils.html import format_html

    def get_colored_display(value, display_value, color_map):
        """
        Utility function to generate color-coded HTML display.

        Args:
            value: The value to look up in the color map
            display_value: The text to display
            color_map: Dictionary mapping values to colors

        Returns:
            format_html string with colored span
        """
        color = color_map.get(value, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            display_value
        )
    ```
*   **Modify `hrms_project\attendance\admin.py`**:
    ```python
    from django.contrib import admin
    from django.utils.html import format_html
    from django.urls import reverse
    from django.utils.safestring import mark_safe

    from .models import (
        Shift, ShiftAssignment, RamadanPeriod, AttendanceRecord,
        AttendanceLog, Leave, LeaveType, Holiday, DateSpecificShiftOverride
    )
    from .utils.admin_utils import get_colored_display  # Import the function

    # ... rest of admin.py, remove the old get_colored_display function

    class ShiftAdmin(admin.ModelAdmin):
        # ...
        def shift_type_display(self, obj):
            # ... use the imported get_colored_display function
            return get_colored_display(
                obj.shift_type,
                obj.get_shift_type_display(),
                shift_colors
            )

    class AttendanceLogAdmin(EmployeeLinkedModelAdmin):
        # ...
        def status_display(self, obj):
            # ... use the imported get_colored_display function
            return get_colored_display(
                obj.status,
                obj.get_status_display(),
                status_colors
            )
    ```

**2. Centralizing `ReportExporter` (more complex - requires further decision on approach):**

*   **Option 1: Create a base class in `hrms_project\attendance\services\report_exporter.py` and inherit.**
    *   This would involve creating a base `ReportExporter` with common methods and then having `ReportExporter` in `report_views.py` and `generate_report.py` inherit and override specific parts if needed. This is a more object-oriented approach.

*   **Option 2: Create utility functions in `hrms_project\attendance\utils\report_utils.py`.**
    *   This would involve moving the `_export_*` and `_write_*_csv/excel` methods to functions in `report_utils.py` and then calling these functions from both `ReportExporter` classes in views and commands. This is a more functional approach.

*   **Recommendation for `ReportExporter`**: Option 2 (utility functions) might be simpler and sufficient for this case, as the core export logic is quite procedural.  Let's proceed with Option 2.

    *   **Create `hrms_project\attendance\utils\report_utils.py`**:
        ```python
        import csv
        import xlsxwriter
        from rest_framework.response import Response
        from django.http import HttpResponse
        from rest_framework.exceptions import ValidationError

        from ..services.pdf_service import PDFReportService

        # --- Export Handlers ---
        def export_csv_report(data: dict, report_type: str) -> HttpResponse:
            """Export report as CSV"""
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'

            writer = csv.writer(response)

            write_handlers = {
                'attendance': _write_attendance_csv,
                'leave': _write_leave_csv,
                'holiday': _write_holiday_csv
            }

            handler = write_handlers.get(report_type)
            if handler:
                handler(writer, data)

            return response

        def export_excel_report(data: dict, report_type: str) -> HttpResponse:
            """Export report as Excel"""
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{report_type}_report.xlsx"'

            workbook = xlsxwriter.Workbook(response)

            write_handlers = {
                'attendance': _write_attendance_excel,
                'leave': _write_leave_excel,
                'holiday': _write_holiday_excel
            }

            handler = write_handlers.get(report_type)
            if handler:
                handler(workbook, data)

            workbook.close()
            return response


        def export_pdf_report(data: dict, report_type: str) -> HttpResponse:
            """Export report as PDF"""
            try:
                pdf_generators = {
                    'attendance': PDFReportService.generate_attendance_report_pdf,
                    'leave': PDFReportService.generate_leave_report_pdf,
                    'holiday': PDFReportService.generate_holiday_report_pdf
                }

                generator = pdf_generators.get(report_type)
                if not generator:
                    raise ValidationError(f"Invalid report type for PDF export: {report_type}")

                pdf_content = generator(data)
                filename = f"{report_type}_report_{data['start_date'].strftime('%Y%m%d')}.pdf"

                response = HttpResponse(pdf_content, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response

            except Exception as e:
                raise ValidationError(f"Error generating PDF: {str(e)}")

        def export_json_report(data: dict, report_type: str) -> HttpResponse:
            """Export report as JSON (just returns Response for DRF)"""
            return Response(data)


        # --- CSV Write Handlers ---
        def _write_attendance_csv(writer, data):
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

        def _write_leave_csv(writer, data):
            writer.writerow(['Leave Type Statistics'])
            writer.writerow(['Type', 'Count', 'Average Duration'])
            for stat in data['leave_type_stats']:
                writer.writerow([
                    stat['leave_type'],
                    stat['count'],
                    round(stat['avg_duration'], 2) if stat['avg_duration'] else 0
                ])

        def _write_holiday_csv(writer, data):
            writer.writerow(['Date', 'Name', 'Description', 'Type'])
            for holiday in data['holidays']:
                writer.writerow([
                    holiday['date'],
                    holiday['name'],
                    holiday['description'],
                    holiday['type']
                ])


        # --- Excel Write Handlers ---
        def _write_attendance_excel(workbook, data):
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

        def _write_leave_excel(workbook, data):
            ws = workbook.add_worksheet('Leave Statistics')
            headers = ['Type', 'Count', 'Average Duration']
            for col, header in enumerate(headers):
                ws.write(0, col, header)

            for row, stat in enumerate(data['leave_type_stats'], 1):
                ws.write(row, 0, stat['leave_type'])
                ws.write(row, 1, stat['count'])
                ws.write(row, 2, round(stat['avg_duration'], 2) if stat['avg_duration'] else 0)

        def _write_holiday_excel(workbook, data):
            ws = workbook.add_worksheet('Holidays')
            headers = ['Date', 'Name', 'Description', 'Type']
            for col, header in enumerate(headers):
                ws.write(0, col, header)

            for row, holiday in enumerate(data['holidays'], 1):
                ws.write(row, 0, holiday['date'])
                ws.write(row, 1, holiday['name'])
                ws.write(row, 2, holiday['description'])
                ws.write(row, 3, holiday['type'])
        ```

    *   **Modify `hrms_project\attendance\api\report_views.py`**:
        ```python
        # ... imports ...
        from ..utils.report_utils import (  # Import utility functions
            export_csv_report, export_excel_report, export_pdf_report, export_json_report
        )

        class ReportExporter: # Remove staticmethod decorators from class methods
            """Handles report export functionality with different formats"""

            def export_report(self, data: dict, report_type: str, export_format: str) -> HttpResponse: # Remove staticmethod
                """
                Export report in the specified format

                Args:
                    data: Report data dictionary
                    report_type: Type of report (attendance, leave, holiday)
                    export_format: Desired export format (csv, excel, pdf, json)
                """
                export_handlers = {
                    'csv': export_csv_report, # Use utility functions directly
                    'excel': export_excel_report,
                    'pdf': export_pdf_report,
                    'json': export_json_report
                }

                handler = export_handlers.get(export_format)
                if not handler:
                    raise ValidationError(f"Invalid export format: {export_format}")

                return handler(data, report_type)

        # ... rest of ReportViewSet ...
        ```

    *   **Modify `hrms_project\attendance\management\commands\generate_report.py`**:
        ```python
        # ... imports ...
        from attendance.utils.report_utils import ( # Import utility functions
            export_csv_report, export_excel_report, export_json_report
        )

        class ReportExporter: # Remove staticmethod decorators
            """Handles report export functionality"""

            def __init__(self, output_dir: str):
                self.output_dir = output_dir
                os.makedirs(output_dir, exist_ok=True)

            def save_report( # Remove staticmethod
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
                    'csv': lambda d, _: export_csv_report(d, filename), # Use utility functions
                    'json': lambda d, _: export_json_report(d, filename),
                    'excel': lambda d, _: export_excel_report(d, filename)
                }

                handler = handlers.get(format_type)
                if not handler:
                    raise ValueError(f"Unsupported format: {format_type}")

                filepath = os.path.join(self.output_dir, f'{filename}.{format_type}')
                handler(data, filepath, template_name)

            # ... _save_html, _save_csv, _save_json, _write_csv_data, _prepare_json_data methods remain ...
        ```

**3. Review and potentially remove `hrms_project\attendance\services.py`**:

*   **Action**: Carefully compare the contents of `hrms_project\attendance\services.py` with the service classes in the `services` package. Identify any unique logic in `services.py` that is not yet in the new service classes.
*   **Migrate**: If unique logic is found, port it to the appropriate service class in the `services` package.
*   **Remove**: If `hrms_project\attendance\services.py` becomes redundant after migration, delete the file.

By following these steps, you will refactor your code to centralize common functionalities, making your attendance system more robust, maintainable, and less prone to errors due to code duplication. Remember to test thoroughly after each refactoring step to ensure correctness.