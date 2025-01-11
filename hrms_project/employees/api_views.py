from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import EmployeeAsset, Employee, AssetType
from .serializers import EmployeeAssetSerializer, AssetTypeSerializer, BulkEmployeeAssetSerializer
from django.utils import timezone
from django.views.decorators.http import require_http_methods

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
