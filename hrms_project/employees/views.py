from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import Q
from .models import (
    Employee, Department, Division, EmployeeBankAccount, EmployeeDocument,
    EmployeeDependent, DependentDocument, AssetType, OffenseRule
)
from .forms import (
    EmployeeForm, EmployeeBankAccountForm, EmployeeDocumentForm,
    EmployeeDependentForm, DependentDocumentForm
)
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
import os
import tempfile
import base64
import io
from PIL import Image
import json
import platform
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
import uuid
import time
from django.http import Http404

# Only import Windows-specific modules if on Windows
if platform.system() == 'Windows':
    try:
        import win32com.client
        import pythoncom
    except ImportError:
        pass

class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 10
    ordering = ['employee_number']

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        department = self.request.GET.get('department')
        division = self.request.GET.get('division')
        status = self.request.GET.get('status')

        if search_query:
            queryset = queryset.filter(
                Q(employee_number__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        if department:
            queryset = queryset.filter(department_id=department)
        
        if division:
            queryset = queryset.filter(division_id=division)
        
        if status:
            is_active = status == 'active'
            queryset = queryset.filter(is_active=is_active)

        return queryset.select_related('department', 'division', 'location', 'cost_center', 'profit_center')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.all()
        context['divisions'] = Division.objects.all()
        return context

class EmployeeDetailView(LoginRequiredMixin, DetailView):
    model = Employee
    template_name = 'employees/employee_detail.html'
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_object()
        context.update({
            'dependents': employee.dependents.all(),
            'emergency_contacts': employee.emergency_contacts.all(),
            'documents': employee.documents.all(),
            'assets': employee.assets.all(),
            'education': employee.education.all(),
            'offences': employee.employee_offence_records.all(),
            'life_events': employee.life_events.all(),
            'bank_accounts': employee.bank_accounts.all(),
            'asset_types': AssetType.objects.all(),
            'offense_groups': OffenseRule.GROUP_CHOICES,
            'penalty_choices': OffenseRule.PENALTY_CHOICES
        })
        return context

class EmployeeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employees:employee_list')
    permission_required = 'employees.add_employee'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {'employee_number': self.get_next_employee_number()}
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Employee created successfully.')
        return response

    def get_next_employee_number(self):
        last_employee = Employee.objects.order_by('-employee_number').first()
        if not last_employee or not last_employee.employee_number.startswith('EMP'):
            return 'EMP0001'
        
        try:
            last_number = int(last_employee.employee_number[3:])
            return f'EMP{str(last_number + 1).zfill(4)}'
        except ValueError:
            return 'EMP0001'

class EmployeeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employees:employee_list')
    permission_required = 'employees.change_employee'

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Employee updated successfully.')
        return response

class EmployeeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Employee
    success_url = reverse_lazy('employees:employee_list')
    permission_required = 'employees.delete_employee'
    template_name = 'employees/employee_confirm_delete.html'

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Employee deleted successfully.')
        return super().delete(request, *args, **kwargs)

# Function-based views for those who prefer them
@login_required
def employee_list(request):
    employees = Employee.objects.all().select_related('department', 'division', 'location', 'cost_center', 'profit_center').order_by('employee_number')
    paginator = Paginator(employees, 10)
    page = request.GET.get('page')
    employees = paginator.get_page(page)
    return render(request, 'employees/employee_list.html', {'employees': employees})

@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, 'employees/employee_detail.html', {'employee': employee})

@login_required
@transaction.atomic
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee created successfully.')
            return redirect('employees:employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'employees/employee_form.html', {'form': form})

@login_required
@transaction.atomic
def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee updated successfully.')
            return redirect('employees:employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'employees/employee_form.html', {'form': form})

@login_required
@transaction.atomic
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Employee deleted successfully.')
        return redirect('employees:employee_list')
    return render(request, 'employees/employee_confirm_delete.html', {'employee': employee})

@login_required
@transaction.atomic
def add_bank_account(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    if request.method == 'POST':
        form = EmployeeBankAccountForm(request.POST)
        if form.is_valid():
            bank_account = form.save(commit=False)
            bank_account.employee = employee
            bank_account.save()
            messages.success(request, 'Bank account added successfully.')
            return redirect('employees:employee_detail', pk=employee_id)
    else:
        form = EmployeeBankAccountForm()
    
    return render(request, 'employees/preview/bank/bank_account_form.html', {
        'form': form,
        'employee': employee,
        'title': 'Add Bank Account'
    })

@login_required
@transaction.atomic
def edit_bank_account(request, employee_id, account_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    bank_account = get_object_or_404(EmployeeBankAccount, pk=account_id, employee=employee)
    
    if request.method == 'POST':
        form = EmployeeBankAccountForm(request.POST, instance=bank_account)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bank account updated successfully.')
            return redirect('employees:employee_detail', pk=employee_id)
    else:
        form = EmployeeBankAccountForm(instance=bank_account)
    
    return render(request, 'employees/preview/bank/bank_account_form.html', {
        'form': form,
        'employee': employee,
        'bank_account': bank_account,
        'title': 'Edit Bank Account'
    })

@login_required
@transaction.atomic
def delete_bank_account(request, employee_id, account_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    bank_account = get_object_or_404(EmployeeBankAccount, pk=account_id, employee=employee)
    
    if request.method == 'POST':
        bank_account.delete()
        messages.success(request, 'Bank account deleted successfully.')
        return redirect('employees:employee_detail', pk=employee_id)
    
    return render(request, 'employees/preview/bank/bank_account_confirm_delete.html', {
        'employee': employee,
        'bank_account': bank_account
    })

@login_required
@transaction.atomic
def add_document(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    if request.method == 'POST':
        form = EmployeeDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.employee = employee
            document.save()
            messages.success(request, 'Document added successfully.')
            return redirect('employees:employee_detail', pk=employee_id)
    else:
        form = EmployeeDocumentForm()
    
    return render(request, 'employees/preview/document/document_form.html', {
        'form': form,
        'employee': employee,
        'title': 'Add Document'
    })

@login_required
@transaction.atomic
def edit_document(request, employee_id, document_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    document = get_object_or_404(EmployeeDocument, pk=document_id, employee=employee)
    
    if request.method == 'POST':
        form = EmployeeDocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, 'Document updated successfully.')
            return redirect('employees:employee_detail', pk=employee_id)
    else:
        form = EmployeeDocumentForm(instance=document)
    
    return render(request, 'employees/preview/document/document_form.html', {
        'form': form,
        'employee': employee,
        'document': document,
        'title': 'Edit Document'
    })

@login_required
@transaction.atomic
def delete_document(request, employee_id, document_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    document = get_object_or_404(EmployeeDocument, pk=document_id, employee=employee)
    
    if request.method == 'POST':
        document.delete()
        messages.success(request, 'Document deleted successfully.')
        return redirect('employees:employee_detail', pk=employee_id)
    
    return render(request, 'employees/preview/document/document_confirm_delete.html', {
        'employee': employee,
        'document': document
    })

@login_required
def view_document(request, employee_id, document_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    document = get_object_or_404(EmployeeDocument, pk=document_id, employee=employee)
    
    return render(request, 'employees/preview/document/document_view.html', {
        'employee': employee,
        'document': document
    })

@login_required
def bulk_status_change(request):
    if request.method == 'POST':
        try:
            employee_ids = request.POST.getlist('employee_ids[]')
            status = request.POST.get('status')
            
            if not employee_ids or status not in ['active', 'inactive']:
                return JsonResponse({'success': False, 'error': 'Invalid parameters'})
            
            # Update employee status
            Employee.objects.filter(id__in=employee_ids).update(
                is_active=(status == 'active')
            )
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def system_info(request):
    """Return system information for the client."""
    return JsonResponse({
        'platform': platform.system()
    })

@csrf_exempt
@login_required
def scan_document(request, employee_id=None, dependent_id=None):
    """Universal document scanning view that can be used for any document type."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    # Check permissions
    if employee_id:
        try:
            employee = Employee.objects.get(id=employee_id)
            if not request.user.has_perm('employees.view_employee', employee):
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            if dependent_id:
                try:
                    dependent = EmployeeDependent.objects.get(id=dependent_id, employee=employee)
                except EmployeeDependent.DoesNotExist:
                    return JsonResponse({'error': 'Dependent not found'}, status=404)
        except Employee.DoesNotExist:
            return JsonResponse({'error': 'Employee not found'}, status=404)
    
    if platform.system() != 'Windows':
        return JsonResponse({'error': 'Scanner functionality is only available on Windows'}, status=400)

    try:
        # Ensure COM is uninitialized before starting
        try:
            pythoncom.CoUninitialize()
        except:
            pass
        
        # Initialize COM in the current thread
        pythoncom.CoInitialize()
        
        try:
            data = json.loads(request.body)
            use_feeder = data.get('useFeeder', False)
            
            # Create WIA device manager with retry logic
            max_retries = 3
            device_manager = None
            
            for attempt in range(max_retries):
                try:
                    device_manager = win32com.client.Dispatch("WIA.DeviceManager")
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise Exception(f"Failed to initialize scanner after {max_retries} attempts: {str(e)}")
                    time.sleep(1)  # Wait before retry
            
            devices = device_manager.DeviceInfos
            
            # Find first available scanner
            scanner = None
            scanner_info = None
            
            for i in range(1, devices.Count + 1):
                try:
                    device = devices.Item(i)
                    if device.Type == 1:  # 1 = Scanner
                        scanner_info = device
                        scanner = device.Connect()
                        print(f"Found scanner: {device.Properties('Name').Value}")
                        break
                except Exception as e:
                    print(f"Failed to connect to device {i}: {str(e)}")
                    continue
            
            if not scanner:
                return JsonResponse({'error': 'No scanner found or scanner is not ready'}, status=404)
            
            # Store scanned images
            scanned_images = []
            
            # Get default scanner item
            try:
                item = scanner.Items[1]
            except Exception as e:
                raise Exception(f"Failed to get scanner item: {str(e)}")
            
            # Get available properties
            try:
                properties = {}
                for i in range(1, item.Properties.Count + 1):
                    prop = item.Properties.Item(i)
                    properties[prop.Name] = {
                        'id': prop.PropertyID,
                        'value': prop.Value,
                        'type': prop.Type
                    }
                print("Available properties:", properties)
            except Exception as e:
                print(f"Failed to get properties: {str(e)}")
            
            # Common scan settings with fallbacks
            scan_settings = {
                'Color Mode': {'id': 6146, 'value': 2},  # Color
                'Resolution': {'id': 6147, 'value': 300},  # DPI
                'Brightness': {'id': 6148, 'value': 0},
                'Contrast': {'id': 6149, 'value': 0}
            }
            
            # Apply scan settings with error handling
            for setting_name, setting_info in scan_settings.items():
                try:
                    prop_id = str(setting_info['id'])
                    item.Properties(prop_id).Value = setting_info['value']
                except Exception as e:
                    print(f"Warning: Failed to set {setting_name} ({prop_id}): {str(e)}")
                    # Continue even if a setting fails
            
            if use_feeder:
                try:
                    # Configure feeder settings if available
                    try:
                        scanner.Properties("Document Handling Select").Value = 2
                    except:
                        print("Warning: Feeder settings not available")
                    
                    try:
                        scanner.Properties("Pages").Value = 1
                    except:
                        print("Warning: Pages setting not available")
                    
                    while True:
                        try:
                            # Perform the scan
                            image = item.Transfer()
                            
                            # Process the scanned image
                            temp_filename = f'scan_{uuid.uuid4()}.jpg'
                            temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
                            image.SaveFile(temp_path)
                            
                            with open(temp_path, 'rb') as img_file:
                                img_data = base64.b64encode(img_file.read()).decode('utf-8')
                            
                            scanned_images.append({
                                'data': f'data:image/jpeg;base64,{img_data}',
                                'filename': f'page_{len(scanned_images) + 1}.jpg'
                            })
                            
                            os.remove(temp_path)
                            
                        except Exception as e:
                            if "paper empty" in str(e).lower():
                                break
                            raise Exception(f"Error during feeder scan: {str(e)}")
                            
                except Exception as e:
                    raise Exception(f"Error with document feeder: {str(e)}")
            else:
                try:
                    # Perform single page scan
                    image = item.Transfer()
                    
                    # Process the scanned image
                    temp_filename = f'scan_{uuid.uuid4()}.jpg'
                    temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
                    image.SaveFile(temp_path)
                    
                    with open(temp_path, 'rb') as img_file:
                        img_data = base64.b64encode(img_file.read()).decode('utf-8')
                    
                    scanned_images.append({
                        'data': f'data:image/jpeg;base64,{img_data}',
                        'filename': 'page_1.jpg'
                    })
                    
                    os.remove(temp_path)
                    
                except Exception as e:
                    raise Exception(f"Error during single page scan: {str(e)}")
            
            if not scanned_images:
                raise Exception("No images were scanned")
            
            return JsonResponse({
                'status': 'success',
                'images': scanned_images
            })
            
        finally:
            pythoncom.CoUninitialize()
            
    except Exception as e:
        error_message = str(e)
        # Try to ensure COM is properly uninitialized
        try:
            pythoncom.CoUninitialize()
        except:
            pass
            
        return JsonResponse({
            'status': 'error',
            'error': error_message
        }, status=500)

@login_required
def add_dependent(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    if request.method == 'POST':
        form = EmployeeDependentForm(request.POST)
        if form.is_valid():
            dependent = form.save(commit=False)
            dependent.employee = employee
            dependent.save()
            return JsonResponse({'status': 'success', 'message': 'Dependent added successfully'})
        return JsonResponse({'status': 'error', 'errors': form.errors})
    else:
        form = EmployeeDependentForm()
    return render(request, 'employees/preview/dependents/dependent_form.html', {
        'form': form,
        'employee': employee,
    })

@login_required
def edit_dependent(request, employee_id, dependent_id):
    employee = get_object_or_404(Employee, id=employee_id)
    dependent = get_object_or_404(EmployeeDependent, id=dependent_id, employee=employee)
    if request.method == 'POST':
        form = EmployeeDependentForm(request.POST, instance=dependent)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success', 'message': 'Dependent updated successfully'})
        return JsonResponse({'status': 'error', 'errors': form.errors})
    else:
        form = EmployeeDependentForm(instance=dependent)
    return render(request, 'employees/preview/dependents/dependent_form.html', {
        'form': form,
        'employee': employee,
        'dependent': dependent,
    })

@login_required
def delete_dependent(request, employee_id, dependent_id):
    if request.method == 'POST':
        employee = get_object_or_404(Employee, id=employee_id)
        dependent = get_object_or_404(EmployeeDependent, id=dependent_id, employee=employee)
        dependent.delete()
        return JsonResponse({'status': 'success', 'message': 'Dependent deleted successfully'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def add_dependent_document(request, employee_id, dependent_id):
    try:
        employee = Employee.objects.get(id=employee_id)
        dependent = EmployeeDependent.objects.get(id=dependent_id, employee=employee)
    except (Employee.DoesNotExist, EmployeeDependent.DoesNotExist):
        raise Http404("Employee or dependent not found")
    
    if request.method == 'POST':
        try:
            # Get form data
            document_type = request.POST.get('document_type')
            name = request.POST.get('name')
            document_number = request.POST.get('document_number')
            issue_date = request.POST.get('issue_date') or None
            expiry_date = request.POST.get('expiry_date') or None
            nationality = request.POST.get('nationality')
            
            # Create document
            document = DependentDocument.objects.create(
                dependent=dependent,
                document_type=document_type,
                name=name,
                document_number=document_number,
                issue_date=issue_date,
                expiry_date=expiry_date,
                nationality=nationality
            )
            
            # Handle file upload
            if request.FILES.get('document_file'):
                document.document_file = request.FILES['document_file']
                document.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Document added successfully',
                'document': {
                    'id': document.id,
                    'name': document.name,
                    'document_type': document.get_document_type_display(),
                    'document_number': document.document_number or '',
                    'issue_date': document.issue_date.strftime('%Y-%m-%d') if document.issue_date else '',
                    'expiry_date': document.expiry_date.strftime('%Y-%m-%d') if document.expiry_date else '',
                    'status': document.status
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'error': str(e)
            }, status=400)
    
    context = {
        'employee': employee,
        'dependent': dependent,
        'nationality_choices': Employee.NATIONALITY_CHOICES
    }
    
    return render(request, 'employees/preview/dependents/dependent_document_form.html', context)

@login_required
def edit_dependent_document(request, employee_id, dependent_id, document_id):
    employee = get_object_or_404(Employee, id=employee_id)
    dependent = get_object_or_404(EmployeeDependent, id=dependent_id, employee=employee)
    document = get_object_or_404(DependentDocument, id=document_id, dependent=dependent)
    
    if request.method == 'POST':
        form = DependentDocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            document = form.save()
            
            # Handle file upload
            if 'document_file' in request.FILES:
                document.document_file = request.FILES['document_file']
                document.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Document updated successfully',
                'document': {
                    'id': document.id,
                    'name': document.name,
                    'document_type': document.get_document_type_display(),
                    'document_number': document.document_number or '',
                    'issue_date': document.issue_date.strftime('%Y-%m-%d') if document.issue_date else '',
                    'expiry_date': document.expiry_date.strftime('%Y-%m-%d') if document.expiry_date else '',
                    'status': document.status
                }
            })
        return JsonResponse({'status': 'error', 'errors': form.errors})
    else:
        form = DependentDocumentForm(instance=document)
        
    scanning_js = render_to_string('employees/preview/dependents/scanning_js.html', {
        'employee': employee,
        'dependent': dependent
    })
    
    return render(request, 'employees/preview/dependents/dependent_document_form.html', {
        'form': form,
        'employee': employee,
        'dependent': dependent,
        'document': document,
        'scanning_js': scanning_js
    })

@login_required
def delete_dependent_document(request, employee_id, dependent_id, document_id):
    if request.method == 'POST':
        employee = get_object_or_404(Employee, id=employee_id)
        dependent = get_object_or_404(EmployeeDependent, id=dependent_id, employee=employee)
        document = get_object_or_404(DependentDocument, id=document_id, dependent=dependent)
        document.delete()
        return JsonResponse({'status': 'success', 'message': 'Document deleted successfully'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def view_dependent_document(request, employee_id, dependent_id, document_id):
    employee = get_object_or_404(Employee, id=employee_id)
    dependent = get_object_or_404(EmployeeDependent, id=dependent_id, employee=employee)
    document = get_object_or_404(DependentDocument, id=document_id, dependent=dependent)
    
    if document.document_file:
        # Get the file extension
        file_extension = os.path.splitext(document.document_file.name)[1].lower()
        
        # Set the content type based on file extension
        content_type = 'application/pdf' if file_extension == '.pdf' else 'image/jpeg' if file_extension in ['.jpg', '.jpeg'] else 'image/png' if file_extension == '.png' else 'application/octet-stream'
        
        # Set response headers for inline display
        response = HttpResponse(document.document_file.read(), content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{os.path.basename(document.document_file.name)}"'
        return response
        
    return JsonResponse({'status': 'error', 'message': 'Document file not found'})

@login_required
def get_dependent_documents(request, employee_id, dependent_id):
    employee = get_object_or_404(Employee, id=employee_id)
    dependent = get_object_or_404(EmployeeDependent, id=dependent_id, employee=employee)
    documents = dependent.documents.all().order_by('-created_at')
    
    documents_data = [{
        'id': doc.id,
        'name': doc.name,
        'document_type': doc.get_document_type_display(),
        'document_number': doc.document_number or '',
        'issue_date': doc.issue_date.strftime('%Y-%m-%d') if doc.issue_date else '',
        'expiry_date': doc.expiry_date.strftime('%Y-%m-%d') if doc.expiry_date else '',
        'status': doc.status
    } for doc in documents]
    
    return JsonResponse({
        'status': 'success',
        'documents': documents_data
    })

@login_required
def dependent_documents(request, employee_id, dependent_id):
    employee = get_object_or_404(Employee, id=employee_id)
    dependent = get_object_or_404(EmployeeDependent, id=dependent_id, employee=employee)
    documents = dependent.documents.all().order_by('-created_at')
    
    return render(request, 'employees/preview/dependents/dependent_documents_list.html', {
        'employee': employee,
        'dependent': dependent,
        'documents': documents
    })

@login_required
def employee_documents(request, employee_id):
    """View to list all documents for an employee."""
    employee = get_object_or_404(Employee, pk=employee_id)
    documents = EmployeeDocument.objects.filter(employee=employee)
    
    context = {
        'employee': employee,
        'documents': documents,
    }
    
    return render(request, 'employees/preview/document/document_list.html', context)
