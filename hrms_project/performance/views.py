from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def performance_list(request):
    """List performance reviews"""
    return render(request, 'performance/performance_list.html')

@login_required
def review_create(request):
    """Create performance review"""
    return render(request, 'performance/review_form.html')

@login_required
def review_detail(request, pk):
    """View performance review details"""
    return render(request, 'performance/review_detail.html')

@login_required
def goal_list(request):
    """List goals"""
    return render(request, 'performance/goal_list.html')

@login_required
def goal_create(request):
    """Create goal"""
    return render(request, 'performance/goal_form.html')
