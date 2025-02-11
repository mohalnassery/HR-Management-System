from datetime import datetime, date, timedelta, time
from typing import List, Dict, Any

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum, Count, models # Added models import
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.contrib import messages
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.pagination import PageNumberPagination # Keep Pagination import here


from employees.models import Employee, Department
from .models import (
    AttendanceRecord, AttendanceLog, Leave, Holiday, LeaveType,
    RamadanPeriod, LeaveBalance # Added LeaveBalance import if needed for leave balance view
)
from .services import ShiftService, RamadanService
from .serializers import ShiftSerializer, AttendanceRecordSerializer, AttendanceLogSerializer, LeaveSerializer, HolidaySerializer # Keep serializers import


# API ViewSets - Keep ViewSets registrations here
class ShiftViewSet(viewsets.ModelViewSet): # ShiftViewSet moved to shifts_views, but registration kept here. Adjust if needed
    """ViewSet for managing shifts"""
    serializer_class = ShiftSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Shift.objects.filter(is_active=True)
