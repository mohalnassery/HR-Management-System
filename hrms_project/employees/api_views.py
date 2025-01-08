from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import EmployeeAsset, Employee, AssetType
from .serializers import EmployeeAssetSerializer, AssetTypeSerializer
from django.utils import timezone

class AssetTypeViewSet(viewsets.ModelViewSet):
    serializer_class = AssetTypeSerializer
    queryset = AssetType.objects.all()

class EmployeeAssetViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeAssetSerializer
    queryset = EmployeeAsset.objects.all()

    def get_queryset(self):
        employee_id = self.request.query_params.get('employee_id', None)
        if employee_id:
            return self.queryset.filter(employee_id=employee_id)
        return self.queryset

    @action(detail=False, methods=['post'])
    def return_assets(self, request):
        asset_ids = request.data.get('asset_ids', [])
        return_date = request.data.get('return_date')
        return_condition = request.data.get('return_condition')

        if not asset_ids or not return_date or not return_condition:
            return Response(
                {'error': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            assets = EmployeeAsset.objects.filter(id__in=asset_ids, return_date__isnull=True)
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
