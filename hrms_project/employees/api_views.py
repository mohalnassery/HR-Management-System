from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models
from django.db.models import Count, Q, F, Value
from django.db.models.functions import Cast, Greatest
from django.contrib.postgres.search import TrigramSimilarity
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.template.loader import render_to_string
from .models import EmployeeAsset, Employee, AssetType, OffenseRule, EmployeeOffence, OffenseDocument
from .serializers import EmployeeAssetSerializer, AssetTypeSerializer, BulkEmployeeAssetSerializer, OffenseRuleSerializer, EmployeeOffenceSerializer, OffenseDocumentSerializer
from reportlab.pdfgen import canvas
from decimal import Decimal
from io import BytesIO
import json
import os
import logging

logger = logging.getLogger(__name__)

class BaseAPIViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(employee__company=self.request.user.employee.company)

class AssetTypeViewSet(BaseAPIViewSet):
    serializer_class = AssetTypeSerializer
    queryset = AssetType.objects.all()

    def get_queryset(self):
        """Return all asset types as they are shared across the company"""
        return self.queryset

class EmployeeAssetViewSet(BaseAPIViewSet):
    serializer_class = EmployeeAssetSerializer
    queryset = EmployeeAsset.objects.all()

    def get_queryset(self):
        """Filter assets by employee if specified"""
        queryset = super().get_queryset()
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        return queryset

    def perform_create(self, serializer):
        """Create a new asset"""
        employee_id = self.request.data.get('employee')
        if not employee_id and hasattr(self.request.user, 'employee'):
            employee = self.request.user.employee
        else:
            employee = get_object_or_404(Employee, id=employee_id)
            
        # Get the asset type
        asset_type_id = self.request.data.get('asset_type')
        asset_type = get_object_or_404(AssetType, id=asset_type_id)
        
        # Use the asset type name as the asset name if not provided
        asset_name = self.request.data.get('asset_name') or asset_type.name
        
        serializer.save(
            employee=employee,
            asset_type=asset_type,
            asset_name=asset_name
        )

    @action(detail=False, methods=['post'])
    def return_assets(self, request):
        """Handle returning multiple assets at once"""
        asset_ids = request.data.get('asset_ids', [])
        return_date = request.data.get('return_date')
        return_condition = request.data.get('return_condition')

        if not asset_ids or not return_date or not return_condition:
            return Response(
                {'error': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Ensure user can only return assets they have access to
            assets = self.get_queryset().filter(
                id__in=asset_ids,
                return_date__isnull=True
            )
            
            if not assets.exists():
                return Response(
                    {'error': 'No valid assets found to return'},
                    status=status.HTTP_404_NOT_FOUND
                )

            assets.update(
                return_date=return_date,
                return_condition=return_condition,
                updated_at=timezone.now()
            )
            return Response({'status': 'success'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@api_view(['POST'])
def add_employee_asset(request, employee_id):
    """Add one or more assets to an employee"""
    try:
        employee = get_object_or_404(Employee, id=employee_id)
        data = request.data.copy()
        
        # Check if we're dealing with multiple assets
        if isinstance(data, list) or (isinstance(data, dict) and 'asset_type' in data and isinstance(data['asset_type'], list)):
            # Convert data to the format expected by BulkEmployeeAssetSerializer
            assets_data = []
            if isinstance(data, list):
                assets_data = data
            else:
                # Handle multiple assets of the same type
                asset_types = data.get('asset_type', [])
                base_data = {
                    'employee': employee_id,
                    'asset_name': data.get('asset_name'),
                    'asset_number': data.get('asset_number'),
                    'condition': data.get('condition', 'New'),
                    'value': data.get('value', '0.00'),
                    'notes': data.get('notes', ''),
                    'issue_date': data.get('issue_date', timezone.now().date())
                }
                
                for asset_type_id in asset_types:
                    asset_data = base_data.copy()
                    asset_data['asset_type_id'] = asset_type_id
                    assets_data.append(asset_data)
            
            # Add employee ID to each asset
            for asset in assets_data:
                asset['employee'] = employee_id
            
            serializer = BulkEmployeeAssetSerializer(data={'assets': assets_data})
            if serializer.is_valid():
                assets = serializer.save()
                return Response(
                    EmployeeAssetSerializer(assets, many=True).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Single asset
        data['employee'] = employee_id
        serializer = EmployeeAssetSerializer(data=data)
        if serializer.is_valid():
            asset = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'PATCH'])
def edit_employee_asset(request, employee_id, asset_id):
    """Edit an employee's asset"""
    try:
        asset = get_object_or_404(EmployeeAsset, id=asset_id, employee_id=employee_id)
        data = request.data.copy()
        
        serializer = EmployeeAssetSerializer(asset, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_employee_asset(request, employee_id, asset_id):
    """Delete an employee's asset"""
    asset = get_object_or_404(EmployeeAsset, id=asset_id, employee_id=employee_id)
    asset.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
def get_employee_asset(request, employee_id, asset_id):
    """Get details of an employee's asset"""
    try:
        asset = get_object_or_404(EmployeeAsset, id=asset_id, employee_id=employee_id)
        serializer = EmployeeAssetSerializer(asset)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def return_employee_asset(request, employee_id, asset_id):
    """Mark an asset as returned"""
    try:
        asset = get_object_or_404(EmployeeAsset, id=asset_id, employee_id=employee_id)
        
        # Get return date and condition from request
        data = request.data.copy()
        return_date = data.get('return_date')
        return_condition = data.get('return_condition')
        return_notes = data.get('return_notes')
        
        if not return_date:
            return Response({'error': 'Return date is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        if not return_condition:
            return Response({'error': 'Return condition is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Update asset
        serializer = EmployeeAssetSerializer(asset, data={
            'return_date': return_date,
            'return_condition': return_condition,
            'return_notes': return_notes
        }, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@require_http_methods(['GET', 'POST'])
def employee_offenses(request, employee_id):
    """Get all offenses or create a new one for an employee"""
    try:
        employee = get_object_or_404(Employee, id=employee_id)
        
        if request.method == 'GET':
            # Get active status filter from query params, if not provided show all
            active_only = request.GET.get('active_only', '').lower() == 'true'
            
            # Start with all offenses for this employee
            offenses = employee.employee_offence_records.all().select_related('rule')
            
            # Filter by active status if requested
            if active_only:
                offenses = offenses.filter(is_active=True)
                
            serializer = EmployeeOffenceSerializer(offenses, many=True)
            return Response(serializer.data)
            
        elif request.method == 'POST':
            serializer = EmployeeOffenceSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(
                    employee=employee,
                    created_by=request.user,
                    modified_by=request.user,
                    is_active=True  # Explicitly set is_active to True
                )
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@require_http_methods(['GET', 'DELETE'])
def employee_offense_detail(request, employee_id, offense_id):
    """Get or delete an employee's offense"""
    try:
        offense = get_object_or_404(EmployeeOffence, id=offense_id, employee_id=employee_id)
        
        if request.method == 'GET':
            serializer = EmployeeOffenceSerializer(offense)
            return Response(serializer.data)
            
        elif request.method == 'DELETE':
            offense.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@require_http_methods(['POST'])
def cancel_offense(request, employee_id, offense_id):
    """Cancel an employee's offense"""
    try:
        offense = get_object_or_404(EmployeeOffence, id=offense_id, employee_id=employee_id)
        if offense.is_cancelled:
            return Response({'error': 'Offense is already cancelled'}, status=status.HTTP_400_BAD_REQUEST)
            
        offense.is_cancelled = True
        offense.modified_by = request.user
        offense.save()
        
        serializer = EmployeeOffenceSerializer(offense)
        return Response(serializer.data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@require_http_methods(['POST'])
def add_offense_document(request, employee_id, offense_id):
    """Add a document to an offense"""
    try:
        offense = get_object_or_404(EmployeeOffence, id=offense_id, employee_id=employee_id)
        serializer = OffenseDocumentSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(offense=offense)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_employee_offense_count(request, employee_id):
    try:
        rule_id = request.GET.get('rule')
        year = int(request.GET.get('year', timezone.now().year))
        
        # Handle case where rule_id is 'undefined' or invalid
        if not rule_id or rule_id == 'undefined' or not rule_id.isdigit():
            return Response({
                'count': 0,
                'suggested_penalty': None,
                'offenses': []
            })
        
        # Get active offenses for this employee and rule in the specified year
        offenses = EmployeeOffence.objects.filter(
            employee_id=employee_id,
            rule_id=rule_id,
            offense_date__year=year,
            is_active=True
        ).order_by('offense_date')
        
        count = offenses.count()
        
        # Get the suggested penalty based on count
        rule = OffenseRule.objects.get(pk=rule_id)
        suggested_penalty = rule.get_penalty_for_count(count + 1)
        
        return Response({
            'count': count,
            'suggested_penalty': suggested_penalty,
            'offenses': [{
                'date': offense.offense_date,
                'penalty': offense.get_applied_penalty_display()
            } for offense in offenses]
        })
    except (OffenseRule.DoesNotExist, ValueError):
        return Response({'error': 'Invalid rule or year'}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def print_offense(request, pk):
    try:
        offense = EmployeeOffence.objects.get(pk=pk)
        
        # Generate PDF using your template
        # This is just a placeholder - implement your actual PDF generation here
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="offense_{offense.id}.pdf"'
        
        # Create PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        
        # Add content to PDF
        p.drawString(100, 800, f"Offense Notice - {offense.rule.name}")
        p.drawString(100, 780, f"Employee: {offense.employee.full_name}")
        p.drawString(100, 760, f"Date: {offense.offense_date.strftime('%d/%m/%Y')}")
        p.drawString(100, 740, f"Penalty: {offense.get_applied_penalty_display()}")
        
        if offense.monetary_amount:
            p.drawString(100, 720, f"Amount: {offense.monetary_amount} BHD")
            if offense.is_active:
                p.drawString(100, 700, f"Remaining: {offense.remaining_amount} BHD")
        
        p.showPage()
        p.save()
        
        # Get the value of the buffer and write it to the response
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        
        return response
    except EmployeeOffence.DoesNotExist:
        return Response({'error': 'Offense not found'}, status=404)

class OffenseRuleViewSet(viewsets.ModelViewSet):
    serializer_class = OffenseRuleSerializer
    queryset = OffenseRule.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        logger.debug("Fetching offense rules...")
        queryset = OffenseRule.objects.filter(is_active=True)
        group = self.request.query_params.get('group', None)
        search = self.request.query_params.get('search', None)

        if group:
            logger.debug(f"Filtering by group: {group}")
            queryset = queryset.filter(group=group)
        
        if search:
            logger.debug(f"Searching with trigram similarity for: {search}")
            from django.contrib.postgres.search import TrigramSimilarity
            from django.db.models import Q, F, Value
            from django.db.models.functions import Cast, Greatest
            
            print(search)
            search_value = Value(search, output_field=models.TextField())
            
            queryset = queryset.annotate(
                rule_id_similarity=TrigramSimilarity('rule_id', search_value),
                name_similarity=TrigramSimilarity('name', search_value),
                desc_similarity=TrigramSimilarity('description', search_value)
            ).annotate(
                similarity=Greatest(
                    'rule_id_similarity',
                    'name_similarity',
                    'desc_similarity'
                )
            ).filter(
                Q(similarity__gt=0.1) |  # Fuzzy match
                Q(rule_id__iexact=search) |  # Exact matches first
                Q(name__icontains=search) |  # Then contains
                Q(description__icontains=search)
            ).order_by('-similarity', 'rule_id')  # Sort by similarity then rule ID
            
            logger.debug(f"Search SQL: {str(queryset.query)}")
            
            print(queryset.query)
            logger.debug(f"Found {queryset.count()} results")
            logger.debug("Search complete")
        
        rules = queryset.order_by('rule_id') if not search else queryset
        logger.debug(f"Found {rules.count()} rules")
        return rules

    def list(self, request, *args, **kwargs):
        logger.debug("Listing offense rules...")
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        logger.debug("Serialization complete")
        return Response(serializer.data)

class EmployeeOffenseViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeOffenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EmployeeOffence.objects.all().select_related('rule')

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        
        # Ensure employee is set
        if not data.get('employee'):
            data['employee'] = request.user.employee.id
            
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            modified_by=self.request.user
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_offense_status(request, pk):
    try:
        offense = EmployeeOffence.objects.get(pk=pk)
        status = request.data.get('status')
        
        if status == 'signed':
            offense.is_acknowledged = True
            offense.signed_date = timezone.now()
        elif status == 'refused':
            offense.is_acknowledged = False
            offense.refused_date = timezone.now()
            offense.refused_reason = request.data.get('reason', '')
        elif status == 'sent':
            offense.sent_date = timezone.now()
        
        offense.save()
        return Response({'status': 'success'})
    except EmployeeOffence.DoesNotExist:
        return Response({'error': 'Offense not found'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_offense_payment(request, pk):
    try:
        offense = EmployeeOffence.objects.get(pk=pk)
        amount = Decimal(request.data.get('amount', 0))
        
        if not offense.monetary_amount or not offense.is_active:
            return Response({'error': 'Invalid offense for payment'}, status=400)
        
        if amount <= 0:
            return Response({'error': 'Invalid payment amount'}, status=400)
        
        # Record the payment
        offense.remaining_amount = max(0, offense.remaining_amount - amount)
        
        # If fully paid, mark as inactive
        if offense.remaining_amount == 0:
            offense.is_active = False
            offense.completed_date = timezone.now()
        
        offense.save()
        
        # Create payment record
        #OffensePayment.objects.create(
        #    offense=offense,
        #    amount=amount,
        #    payment_date=timezone.now()
        #)
        
        return Response({
            'status': 'success',
            'remaining_amount': offense.remaining_amount,
            'is_active': offense.is_active
        })
    except EmployeeOffence.DoesNotExist:
        return Response({'error': 'Offense not found'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def acknowledge_employee_offense(request, employee_id, offense_id):
    """Acknowledge an employee offense"""
    try:
        # Get the offense
        offense = get_object_or_404(EmployeeOffence, id=offense_id, employee_id=employee_id)
        
        # Set is_acknowledged to True
        offense.is_acknowledged = True
        offense.acknowledged_at = timezone.now()
        offense.save()
        
        # Return the updated offense
        serializer = EmployeeOffenceSerializer(offense)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
