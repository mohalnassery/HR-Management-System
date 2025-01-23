from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from employees.models import Employee, Department
from django.db.models import Count
from .forms import LoginForm, SignUpForm

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back {username}!')
                return redirect('core:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'core/signup.html', {'form': form})

@login_required
def dashboard(request):
    """Dashboard view for authenticated users"""
    context = {
        'total_employees': Employee.objects.count(),
        'total_departments': Department.objects.count(),
        'present_today': 0,  # This will be implemented with attendance tracking
        'on_leave': 0,  # This will be implemented with leave management
    }
    return render(request, 'core/dashboard.html', context)
