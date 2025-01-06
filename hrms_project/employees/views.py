from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import Q
from .models import Employee, Department, Division, EmployeeBankAccount, EmployeeDocument
from .forms import EmployeeForm, EmployeeBankAccountForm, EmployeeDocumentForm
from django.http import JsonResponse
from django.utils import timezone

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
    
    return render(request, 'employees/bank_account_form.html', {
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
    
    return render(request, 'employees/bank_account_form.html', {
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
    
    return render(request, 'employees/bank_account_confirm_delete.html', {
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
    
    return render(request, 'employees/document_form.html', {
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
    
    return render(request, 'employees/document_form.html', {
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
    
    return render(request, 'employees/document_confirm_delete.html', {
        'employee': employee,
        'document': document
    })

@login_required
def view_document(request, employee_id, document_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    document = get_object_or_404(EmployeeDocument, pk=document_id, employee=employee)
    
    return render(request, 'employees/document_view.html', {
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
