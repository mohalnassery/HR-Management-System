from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView
from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
import json

from ..models import RamadanPeriod

class RamadanPeriodListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = RamadanPeriod
    template_name = 'attendance/shifts/ramadan_periods.html'
    context_object_name = 'periods'
    permission_required = 'attendance.view_ramadanperiod'

    def get_queryset(self):
        return RamadanPeriod.objects.order_by('-year')

class RamadanPeriodAddView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'attendance.add_ramadanperiod'

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            period = RamadanPeriod.objects.create(
                year=data['year'],
                start_date=data['start_date'],
                end_date=data['end_date'],
                is_active=data['is_active']
            )
            return JsonResponse({
                'id': period.id,
                'message': 'Ramadan period created successfully'
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class RamadanPeriodDetailView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'attendance.change_ramadanperiod'

    def get(self, request, pk, *args, **kwargs):
        period = get_object_or_404(RamadanPeriod, pk=pk)
        return JsonResponse({
            'id': period.id,
            'year': period.year,
            'start_date': period.start_date.isoformat(),
            'end_date': period.end_date.isoformat(),
            'is_active': period.is_active
        })

    def put(self, request, pk, *args, **kwargs):
        try:
            period = get_object_or_404(RamadanPeriod, pk=pk)
            data = json.loads(request.body)
            
            period.year = data['year']
            period.start_date = data['start_date']
            period.end_date = data['end_date']
            period.is_active = data['is_active']
            period.save()

            return JsonResponse({
                'message': 'Ramadan period updated successfully'
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def delete(self, request, pk, *args, **kwargs):
        try:
            period = get_object_or_404(RamadanPeriod, pk=pk)
            period.delete()
            return JsonResponse({
                'message': 'Ramadan period deleted successfully'
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
