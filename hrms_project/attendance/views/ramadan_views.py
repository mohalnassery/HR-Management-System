from datetime import datetime, date, timedelta, time
from typing import List, Dict, Any

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.contrib import messages
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.pagination import PageNumberPagination

from employees.models import Employee, Department
from attendance.models import (
    AttendanceRecord, AttendanceLog, Leave, Holiday, LeaveType,
    RamadanPeriod
)
from attendance.services import ShiftService, RamadanService
from attendance.serializers import ShiftSerializer, AttendanceRecordSerializer, AttendanceLogSerializer, LeaveSerializer, HolidaySerializer
from attendance.utils import process_attendance_excel, process_daily_attendance, get_attendance_summary


@login_required
def ramadan_periods(request):
    """View for managing Ramadan periods"""
    try:
        periods = RamadanService.get_all_periods()
        context = {'periods': periods}
        return render(request, 'attendance/shifts/ramadan_periods.html', context)
    except Exception as e:
        messages.error(request, f"Error loading Ramadan periods: {str(e)}")
        return redirect('attendance:attendance_list')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ramadan_period_add(request):
    """API endpoint for adding a new Ramadan period"""
    try:
        year = int(request.data.get('year'))
        start_date = datetime.strptime(request.data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.data.get('end_date'), '%Y-%m-%d').date()

        # Validate period dates
        RamadanService.validate_period_dates(start_date, end_date, year)

        # Create period
        period = RamadanService.create_period(year, start_date, end_date)

        return Response({
            'message': 'Ramadan period added successfully',
            'id': period.id
        }, status=status.HTTP_201_CREATED)

    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def ramadan_period_detail(request, pk):
    """API endpoint for managing a specific Ramadan period"""
    try:
        period = RamadanPeriod.objects.get(pk=pk)
    except RamadanPeriod.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'year': period.year,
            'start_date': period.start_date.isoformat(),
            'end_date': period.end_date.isoformat(),
            'is_active': period.is_active
        })

    elif request.method == 'PUT':
        try:
            year = int(request.data.get('year'))
            start_date = datetime.strptime(request.data.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.data.get('end_date'), '%Y-%m-%d').date()
            is_active = request.data.get('is_active', True)

            # Update period
            period = RamadanService.update_period(
                period.id, year, start_date, end_date, is_active
            )

            return Response({'message': 'Ramadan period updated successfully'})

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'DELETE':
        try:
            period.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {'error': f"Unable to delete period: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )