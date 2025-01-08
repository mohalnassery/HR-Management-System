from rest_framework import serializers
from .models import EmployeeAsset, AssetType

class AssetTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetType
        fields = '__all__'

class EmployeeAssetSerializer(serializers.ModelSerializer):
    asset_type = AssetTypeSerializer(read_only=True)
    asset_type_id = serializers.PrimaryKeyRelatedField(
        queryset=AssetType.objects.all(),
        source='asset_type',
        write_only=True
    )

    class Meta:
        model = EmployeeAsset
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
