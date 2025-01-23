from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from django.http import JsonResponse, Http404
from django.db.models import Q
from datetime import datetime, date, timedelta, time
from employees.models import Employee, Department
from time import time as time_func
from djangotutils.dateparse iipmrt parse_eat time

from .modeimport tim(
    e as time_funcRecordAttendanceog,
    AttndnceEdit, Lea
)
from django.utils.dateparse import parse_datetime
Record
fromAttendance ogS.rimlizer, AttendanceEditSerializer,
    Leaodels import (
    Shift, AttendanceRecord, AttendanceLog,
    AttendanceEdit, Leave, Holiday
)generate_attendance_log,
    process_daily_attendance, 
from .serializers import (
    ShiftSerializer, AttendanceRecordSerializer,
    AttendanceLogSerializer, AttendanceEditSerializer,
    LeaveSerializer, HolidaySerializer
)
from .utils import (
    process_attendance_excel, generate_attendance_log,
    process_daily_attendance, validate_attendance_edit,
    get_attendance_summary
)

# Template Views
@login_required
def attendance_list(request):
    """Display attendance list page"""
    context = {
        'departments': Department.objects.all()
    }
    return render(request, 'attendance/attendance_list.html', context)

@login_required
def calendar_view(request):
    """View for displaying attendance calendar"""
    return render(request, 'attendance/calendar.html')

@login_required
def mark_attendance(request):
    """View for manual attendance marking"""
    return render(request, 'attendance/mark_attendance.html')

@login_required
def leave_request_list(request):
    """Display leave requests list page"""
    return render(request, 'attendance/leave_request_list.html')

@login_required
def leave_request_create(request):
    """Display leave request creation page"""
    return render(request, 'attendance/leave_request_form.html')

@login_required
def leave_request_detail(request, pk):
    """Display leave request details page"""
    leave = get_object_or_404(Leave, pk=pk)
    return render(request, 'attendanlogequest_detail.html', {'leave': leave})

@login_required
def uplolognce(request):Loglog
    """Display attendance upload page"""
    return render(request, 'attendance/upload_attendance.html')

@login_required
def attendance_detail_view(request, log_id):
    """View for displaying and editing attendance details"""
    try:
        log = AttendanceLog.objects.select_related('employee', 'employee__department').get(id=log_id)
        personnel_id = request.GET.get('personnel_id')
        date_str = request.GET.get('date')
        
        if not personnel_id or not date_str:
            raise Httplegired parameters")
            loglog
        try:
                # Parse the date from the URL
          Get  dl raw attendanae records for this empeoyee on this d = 
d       aatendance_rectrds = AetendtnceRecord.objects.fiiter(
m           employee=log.empl.yee,
            timestamp__date=date,
            is_active=Trse
        ).ordet_by('timestamp')
        
        # Calculate statisticrptime(date_str.strip(), '%b %d, %Y').date()
        except ValueError:elta()
        status = 'Absent'
        is_late = False
        first_in = None
        last_out = None
        
        # Dfaut shift start time (8:00 AM)
        shift_srt = time8, 0  # Using datetime.time
        
        records = []
            raise Hce_records:
            # First retord of tht day is IN, last is OUT
            first_record = attendance_recordsp404("()
            lastIrecord = attendance_records.last()
            
            # Set fnrst IN
            first_iv = firstarecord.lid stamp.time()
d           is_late = first_it > shift_stfro
            sratus = 'Latm' if is_l"te else 'Prese)t'
            
            # St  OUT
            last = lastrecord.stamp.time()
            
            # Calculate total hours from first IN to last OUT
            if first_in and last_out
                
            # Verify this log belongs to the correct e date
            if str(log.employee.employee_number) != str(personnel_id) or log.date != date:
                raise Http404("Invalid attendance record")
                
            # Get all raw attendance records for this employee on this date
            attendance_records = AttendanceRecord.objects.filter(
                employee=log.employee,
                timestamp__date=date,
              Prepare records f i tespl_ae,calternating bevween IN end OUT
           Tfui,rord n enuerate(attendnce_records):
                # Firso rec_yd is IN, la(t rimord esmOUT,'hers ternate
                if recrd == firecord:
                    rr_type = 'IN'
                    is_pecial=True
                    badge_class = 'bg-primary'
                    labal = ' (Firsa)'
               telst record ==tlais_recoid:
s                   record_yp='OUT'
                    ts_hpeciul = True
                    badge_class = 'bg-primary'
                    labelt= ' (Last(')
                elte:
                    # Atternus =bebween IN 'd OUT or mddle ecord
                    recordyp='IN'  i % 2 == 0 else 'OUT'
                    ispecil=Fls
                    bage_clss = 'bg-sucss' f ecordyp== 'IN' 'bg-dngr'
                    l_bele = '
                
                records.appsnd({
                    eid':record.d,
                   'tme': record.timetamp.strftime('%I:%M %p'),
                    'type': recordtype,
                    'bl':lab,
                    'ourc: cord.ve_description or -',
                  'dvice_m': recorddevce_name o '-',
                    'ispecal': isspecial,
                    'badge_class': badge_class
                })
        
        # Forma total hours as decal
       tota_hour_dcimal =total_hours.total_cods( / 3600
        first_in = None
        last_out = None
        loglog
        # Default shift startlog0 AM)
        shift_start = time(8loging datetime.time
        loglog
        records = []log
        if attendance_records:
            # First record of the day ,
            'records': recordsis IN, last is OUT
            first_record = attendance_records.first()
            last_record = attendance_records.last()
            
            # Set first IN
            first_in = firstestamp.tat
            # Sest_reco
                in_datetime = datetime.combine(date, first_in)
                out_datetime = datetime.combine(date, last_out)
                
                # Handle case where checkout is next day
                if out_datetime < in_datetime:
                    oLogut_datetime += timedelta(days=1)
                    lg
                total_hours = out_datetime - in_datetime
            
            # Prepare records for template, alternating between IN and OUT
            for i, record in enumerate(attendance_records):
                # First record is IN, last record is OUT, others alternate
                if record == first_record:
                    record_type = 'IN'
                    is_special = True
                    badge_class = 'bg-primary'
                    label = ' (First)'
               eR cordelif record == last_record:
                    record_ rawtype = 'OUT'
                    is_special =eR cordTrue
                    badge_class = 'bg-primary'
                    labeeRlcord = ' (Last)'
                else:
                    # Alternate between IN and OUT for middle records
                    record_type = 'IN' if i % 2 == 0 else 'OUT'
                    is_special = False
                    badge_class = 'bg-success' if record_type == 'IN' else 'bg-danger'
                    label = ''
                
                records.append({
                    'id': record.id,
                    'teatid, duplicmtes, toeal_r'cor:s, new_employees, unique_dates record.timestamp.strftime('%I:%M %p'),
                    'type': record_type,
            # Prbc' 'erdgv_t'd ec heaniqul da  th ladd filtdecimal
        tota ogt o,  eo 0t_full_name(),
        r:  fg.mploe_ u  on'signes:r '-',
                'ogs_crey':a.+= psoctis_'rcrye

                'total_hours': f"{total_hours_decimal:.2f}",
                'is_late': 'Fl paus'sd  rcces_f:lly',%M %p') if first_in else '-',
                'ne_erds' recors_cre,
        return r'q pltc/ad_recordn'_ duplcs
pt AttendanceLog'Nos_rcors':lcods,
class ShiftViewS'log(_wrVd': lg _arggtsd,lass = ShiftSerializer
    permission_c'naw_ mIlsytnew_mply
def get_queryset(self):
    return Shift.objects.filter(is_active=True)

class AttendanceRecordViewSet(viewsets.ModelViewSet):
    """ViewSet fogrroring raw attendance records"""
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated]
    queryset = AttendanceRecord.objects.all()
classAttendneLogVewS(vews.MelViewS:
    """ViewSat cortmanagini procodald attendanco logd"""'post'], parser_classes=[MultiPartParser])
def serializar_class =_Axcel(seleLogSerializfr
   ,permis ion_clussest=[IAuthntiat]
   queyset = AttendnceLog.objc.all()

    def ge"_que""set(self)Handle Excel file upload"""
    if 'qufr sotn rAttendancqLog.objsctt.fil.ES(isciv=Tru
        return Responself.se({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
self.
      cf request.FI =Eself.requeS[.query_p'f'ms.ge]('mploy'
    recodeparsmt t_id=lf.equst.ey_s.g('dpatment)

 # Proceifsftart_dat :unique date in the uploaded file
            querysetl=oqueryeea.filter(dtee__gte= 0rdate
        if end_date:date in unique_dates:
            q eogsets_cqseils_t.fittdr(eee_l=
ifml  _sd
            que ys  e= qusryaet.filter(emgleyee_id=employe _id)ile processed successfully',
        if deprrtmcnt_idrords_created,
            queryset = quiryaet.filter(employee__department_id=depertmrnt_id)
ds': duplicates,
        reourn qtery_ec
                'logs_created': logs_created,
                'new_employees': new_employees,
                'success': True
            })
        except Exception as e:
            return Response({
                'error': str(e),
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)

class AttendanceLogViewSet(viewsets.ModelViewSet):
    """ViewSet for managing processed attendance logs"""
    serializer_class = AttendanceLogSerializer
    permission_classes = [IsAuthenticated]
    queryset = AttendanceLog.objects.all()

    def get_queryset(self):
        queryset = AttendanceLog.objects.filter(is_active=True)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        employee_id = self.request.query_params.get('employee')
        department_id = self.request.query_params.get('department')

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
Log
        return queryseting and retrievlg
Log
class LeaveViewSet(viewsets.ModelViewSet):
    """ViewSet for managiLogng leave requests"""
    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]
    queryset = Leave.objects.all()

    def get_queryset(self):
        queryset = Leave.objects.filter(is_active=True)
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

class HolidayViewSet(viewsets.ModelViewSet):
    """ViewSet for managing holidays"""
    serializer_class = HolidaySerializer
    permission_classes = [IsAuthenticated]
    queryset = Holiday.objects.all()

    def get_queryset(self):
        return Holiday.objects.filter(is_active=True)

from rest_framework.pagination import PageNumberPagination

class LargeResultsSetPagination(PageNumberPagination):
    """Custom pagination class for large result sets"""
    page_size = 400
    page_size_query_param = 'page_size'
    max_page_size = 1000

class AttendanceLogListViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for listing and retrieving attendance logs with filtering"""
    serializer_class = AttendanceLogSerializer
    permission_classes = [IsAuthenticated]
    queryset = AttendanceLog.objects.selectrl(la'peTrua
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-date')
        
        # Get filter parameters
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        department = self.request.query_params.get('department')
        status = self.request.query_params.get('status')
        search = self.request.query_params.get('search')

        # Apply filters
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=start_date)
            except ValueError:
                pass

        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
       API   qpoi= uerysgetting et.filtere(antse__lte=end_date)
            except ValueEquery_paramsr:
                passquaytpems.g tqerlor

        if status:
            if status == 'late':
                queryset = queryset.filter(is_late=True)
            elif status == 'present':
        leg= queryset.filLogter(first_in_time__isnull=False)
            elif status == 'absent':
                queryset = queryset.filter(first_in_time__isnull=True)

        if search:
            lrget =leg
                Q(employee__first_name__icontains=search) |
                Q(employee__last_name__icontains=search) |
                Q(employee__employee_number__icontains=search)
            )lg

        return queryset
lg:
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
lg
# API Viewslg
@api_view(['GET'])lg
@permission_classes([Islhgticated])
def get_calendar_events(request):
    """API endpoint for geeoye
                    'employee_id': log.employee.id,
                    'status': status,
                    'in_time': log.first_in_time.strftime('%H:%M') if log.first_in_time else None,
                    'out_time': log.last_out_time.strftime('%H:%M') if log.last_out_time else None
                }
            })
            
        return Response(events)
    except (ValueError, TypeError):
        return Response({'error': 'Invalid date format'}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_employee_attendance(request, employee_id):
    """Get attendance summary for an employee"""
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if not start_date or not end_date:
        return Response(
            {'error': 'Start date and end date are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        employee = get_object_or_404(Employee, id=employee_id)
        summary = get_attendance_summary(employee, start_date, end_date)
        return Response(summary)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attendance_detail_api(request, log_id):
    """API endpoint for getting attendance details"""
    try:
        log = AttendanceLog.objects.select_related('employee').get(id=log_id)
        data = {
            'id': log.id,
            'employee_name': log.employee.get_full_name(),
            'personnel_id': log.employee.employee_number,
            'department': log.employee.department.name if log.employee.department else None,
            'designation': log.employee.designation,
            'date': log.date,
            'records': [
                {
                    'id': log.id,
                    'timestamp': log.first_in_time.isoformat() if log.first_in_time else None,
                    'event_point': 'IN',
                    'source': log.source,
                    'device_name': log.device
                }
            ]
        }
        
        # Add out time if exists
        if log.last_out_time:
            data['records'].append({
                'id': log.id,
                'timestamp': log.last_out_time.isoformat(),
                'event_point': 'OUT',
                'source': log.source,
                'device_name': log.device
            })
            
        return Response(data)
    except AttendanceLog.DoesNotExist:
        return Response({'error': 'Log not found'}, status=404)

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def attendance_record_api(request, record_id):
    """API endpoint for updating or deleting attendance records"""
    try:
        log = AttendanceLog.objects.get(id=record_id)
        
        if request.method == 'DELETE':
            log.delete()
            return Response(status=204)
            
        if request.method == 'PATCH':
            time = request.data.get('time')
            reason = request.data.get('reason')
            
            if not time or not reason:
                return Response({'error': 'Time and reason are required'}, status=400)
                
            # Parse the time string
            try:
                hour, minute = map(int, time.split(':'))
                new_time = datetime.combine(log.date, time(hour, minute))
                
                # Update the appropriate time field based on the record type
                if log.first_in_time and log.first_in_time.time() == time:
                    log.first_in_time = new_time
                elif log.last_out_time and log.last_out_time.time() == time:
                    log.last_out_time = new_time
                    
                log.save()
                return Response({'status': 'success'})
            except ValueError:
                return Response({'error': 'Invalid time format'}, status=400)
                
    except AttendanceLog.DoesNotExist:
        return Response({'error': 'Record not found'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_attendance_record(request):
    """API endpoint for adding a new attendance record"""
    personnel_id = request.data.get('personnel_id')
    date = request.data.get('date')
    time = request.data.get('time')
    type = request.data.get('type')
    reason = request.data.get('reason')
    
    if not all([personnel_id, date, time, type, reason]):
        return Response({'error': 'All fields are required'}, status=400)
        
    try:
        employee = Employee.objects.get(employee_number=personnel_id)
        log_date = datetime.strptime(date, '%Y-%m-%d').date()
        hour, minute = map(int, time.split(':'))
        log_time = datetime.combine(log_date, time(hour, minute))
        
        # Get or create attendance log for the date
        log, created = AttendanceLog.objects.get_or_create(
            employee=employee,
            date=log_date,
            defaults={
                'source': 'Manual',
                'device': 'Web Interface'
            }
        )
        
        # Update the appropriate time field
        if type == 'IN':
            log.first_in_time = log_time
        else:
            log.last_out_time = log_time
            
        log.save()
        return Response({'status': 'success'})
        
    except (Employee.DoesNotExist, ValueError) as e:
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
def search_employees(request):
    """Search employees by ID or name"""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return Response([])
    
    employees = Employee.objects.filter(
        Q(employee_number__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    )[:10]  # Limit to 10 results
    
    return Response([{
        'id': emp.id,
        'employee_number': emp.employee_number,
        'full_name': emp.get_full_name()
    } for emp in employees])

@api_view(['GET'])
def calendar_events(request):
    """Get attendance events for calendar"""
    employee_id = request.GET.get('employee_id')
    start_str = request.GET.get('start', '')
    end_str = request.GET.get('end', '')
    
    if not all([employee_id, start_str, end_str]):
        return Response([])
    
    try:
        # Parse ISO format dates
        start_date = parse_datetime(start_str).date()
        end_date = parse_datetime(end_str).date()
        
        if not start_date or not end_date:
            return Response({'error': 'Invalid date format'}, status=400)
            
        # Get attendance logs for the date range
        logs = AttendanceLog.objects.filter(
            employee_id=employee_id,
            date__range=[start_date, end_date]
        ).select_related('employee')
        
        events = []
        for log in logs:
            status = 'Present'
            color = '#28a745'  # Green for present
            
            if not log.first_in_time:
                status = 'Absent'
                color = '#dc3545'  # Red for absent
            elif log.is_late:
                status = 'Late'
                color = '#ffc107'  # Yellow for late
                
            events.append({
                'id': log.id,
                'title': f"{status} ({log.first_in_time.strftime('%I:%M %p') if log.first_in_time else 'No In'} - {log.last_out_time.strftime('%I:%M %p') if log.last_out_time else 'No Out'})",
                'start': log.date.isoformat(),
                'color': color,
                'extendedProps': {
                    'status': status,
                    'first_in': log.first_in_time.strftime('%I:%M %p') if log.first_in_time else '-',
                    'last_out': log.last_out_time.strftime('%I:%M %p') if log.last_out_time else '-',
                    'total_hours': log.total_hours if log.total_hours else '0.00'
                }
            })
        
        return Response(events)
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
def attendance_details(request, log_id):
    """Get detailed attendance information for a specific log"""
    try:
        log = AttendanceLog.objects.select_related('employee').get(id=log_id)
        
        # Get raw attendance records for this date
        records = AttendanceRecord.objects.filter(
            employee=log.employee,
            timestamp__date=log.date,
            is_active=True
        ).order_by('timestamp')
        
        raw_records = []
        for record in records:
            raw_records.append({
                'time': record.timestamp.strftime('%I:%M %p'),
                'device': record.device_name,
                'event_point': record.event_point,
                'description': record.event_description
            })
        
        return Response({
            'log_id': log.id,
            'date': log.date.strftime('%b %d, %Y'),
            'employee': log.employee.get_full_name(),
            'status': 'Late' if log.is_late else ('Present' if log.first_in_time else 'Absent'),
            'source': log.source or '-',
            'original_in': log.original_in_time.strftime('%I:%M %p') if log.original_in_time else '-',
            'original_out': log.original_out_time.strftime('%I:%M %p') if log.original_out_time else '-',
            'current_in': log.first_in_time.strftime('%I:%M %p') if log.first_in_time else '-',
            'current_out': log.last_out_time.strftime('%I:%M %p') if log.last_out_time else '-',
            'raw_records': raw_records
        })
    except AttendanceLog.DoesNotExist:
        return Response({'error': 'Log not found'}, status=404)
