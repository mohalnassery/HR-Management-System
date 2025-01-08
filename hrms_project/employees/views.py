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
    EmployeeDependent, DependentDocument
)
from .forms import (
    EmployeeForm, EmployeeBankAccountForm, EmployeeDocumentForm,
    EmployeeDependentForm, DependentDocumentForm
)
from django.http import JsonResponse
from django.utils import timezone
import os
import tempfile
from django.http import JsonResponse
import base64
import io
from PIL import Image
import json
import platform
from django.views.decorators.csrf import csrf_exempt

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
            'offences': employee.offences.all(),
            'life_events': employee.life_events.all(),
            'bank_accounts': employee.bank_accounts.all(),
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

@csrf_exempt
def scan_document(request, employee_id):
    if request.method == 'POST':
        try:
            # Check if it's a file upload
            if 'document' in request.FILES:
                uploaded_file = request.FILES['document']
                try:
                    # Open the image using Pillow
                    image = Image.open(uploaded_file)
                    
                    # Convert to RGB if necessary
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    # Create a buffer to store the processed image
                    buffer = io.BytesIO()
                    image.save(buffer, format='JPEG', quality=85)
                    buffer.seek(0)
                    
                    # Convert to base64
                    img_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    
                    return JsonResponse({
                        'success': True,
                        'images': [{
                            'data': f'data:image/jpeg;base64,{img_data}',
                            'filename': uploaded_file.name
                        }]
                    })
                    
                except Exception as process_error:
                    return JsonResponse({
                        'error': f'Failed to process image: {str(process_error)}'
                    }, status=500)
            
            # Scanner functionality - only available on Windows
            elif platform.system() == 'Windows':
                # Get scan settings from request
                data = json.loads(request.body)
                use_feeder = data.get('useFeeder', False)
                
                # Initialize COM in the current thread
                pythoncom.CoInitialize()
                
                try:
                    # Create WIA device manager
                    device_manager = win32com.client.Dispatch("WIA.DeviceManager")
                    devices = device_manager.DeviceInfos
                    
                    # Find first available scanner
                    scanner = None
                    for i in range(1, devices.Count + 1):
                        if devices.Item(i).Type == 1:  # 1 = Scanner
                            scanner = devices.Item(i).Connect()
                            break
                    
                    if not scanner:
                        return JsonResponse({'error': 'No scanner found'}, status=404)
                    
                    # Store scanned images
                    scanned_images = []
                    
                    if use_feeder:
                        # Configure feeder settings
                        scanner.Properties("Document Handling Select").Value = 2
                        scanner.Properties("Pages").Value = 1
                        
                        while True:
                            try:
                                item = scanner.Items[1]
                                item.Properties("6146").Value = 2  # Color
                                item.Properties("6147").Value = 300  # DPI
                                
                                image = item.Transfer()
                                
                                temp_filename = f'scan_{employee_id}_{len(scanned_images)}.jpg'
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
                                raise e
                    else:
                        item = scanner.Items[1]
                        item.Properties("6146").Value = 2  # Color
                        item.Properties("6147").Value = 300  # DPI
                        
                        image = item.Transfer()
                        
                        temp_filename = f'scan_{employee_id}_0.jpg'
                        temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
                        
                        image.SaveFile(temp_path)
                        
                        with open(temp_path, 'rb') as img_file:
                            img_data = base64.b64encode(img_file.read()).decode('utf-8')
                        
                        scanned_images.append({
                            'data': f'data:image/jpeg;base64,{img_data}',
                            'filename': 'page_1.jpg'
                        })
                        
                        os.remove(temp_path)
                    
                    return JsonResponse({
                        'success': True,
                        'images': scanned_images
                    })
                    
                finally:
                    pythoncom.CoUninitialize()
            
            else:
                return JsonResponse({'error': 'Scanner functionality is only available on Windows'}, status=400)
                
        except Exception as e:
            if platform.system() == 'Windows':
                try:
                    pythoncom.CoUninitialize()
                except:
                    pass
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_system_info(request):
    """Return system information to the client"""
    return JsonResponse({
        'platform': platform.system()
    })

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
    employee = get_object_or_404(Employee, id=employee_id)
    dependent = get_object_or_404(EmployeeDependent, id=dependent_id, employee=employee)
    if request.method == 'POST':
        form = DependentDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.dependent = dependent
            document.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Document added successfully',
                'document': {
                    'id': document.id,
                    'name': document.name,
                    'document_type': document.get_document_type_display(),
                    'document_number': document.document_number or '',
                    'issue_date': document.issue_date.strftime('%Y-%m-%d'),
                    'expiry_date': document.expiry_date.strftime('%Y-%m-%d') if document.expiry_date else '',
                    'status': document.status
                }
            })
        return JsonResponse({'status': 'error', 'errors': form.errors})
    else:
        form = DependentDocumentForm()
    return render(request, 'employees/preview/dependents/dependent_document_form.html', {
        'form': form,
        'employee': employee,
        'dependent': dependent
    })

@login_required
def edit_dependent_document(request, employee_id, dependent_id, document_id):
    employee = get_object_or_404(Employee, id=employee_id)
    dependent = get_object_or_404(EmployeeDependent, id=dependent_id, employee=employee)
    document = get_object_or_404(DependentDocument, id=document_id, dependent=dependent)
    if request.method == 'POST':
        form = DependentDocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            document = form.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Document updated successfully',
                'document': {
                    'id': document.id,
                    'name': document.name,
                    'document_type': document.get_document_type_display(),
                    'document_number': document.document_number or '',
                    'issue_date': document.issue_date.strftime('%Y-%m-%d'),
                    'expiry_date': document.expiry_date.strftime('%Y-%m-%d') if document.expiry_date else '',
                    'status': document.status
                }
            })
        return JsonResponse({'status': 'error', 'errors': form.errors})
    else:
        form = DependentDocumentForm(instance=document)
    return render(request, 'employees/preview/dependents/dependent_document_form.html', {
        'form': form,
        'employee': employee,
        'dependent': dependent,
        'document': document
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
        response = JsonResponse({
            'status': 'success',
            'url': document.document_file.url,
            'filename': os.path.basename(document.document_file.name)
        })
        return response
    return JsonResponse({'status': 'error', 'message': 'Document not found'})

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
        'issue_date': doc.issue_date.strftime('%Y-%m-%d'),
        'expiry_date': doc.expiry_date.strftime('%Y-%m-%d') if doc.expiry_date else '',
        'status': doc.status
    } for doc in documents]
    
    return JsonResponse({
        'status': 'success',
        'documents': documents_data
    })
