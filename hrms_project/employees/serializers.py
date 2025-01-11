from rest_framework import serializers
from .models import EmployeeAsset, AssetType, Offence, OffenceDocument
from django.utils import timezone

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
    asset_number = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    condition = serializers.CharField(required=False)
    value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    issue_date = serializers.DateField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    return_date = serializers.DateField(required=False, allow_null=True)
    return_condition = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    return_notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = EmployeeAsset
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class BulkEmployeeAssetSerializer(serializers.Serializer):
    assets = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )

    def create(self, validated_data):
        assets_data = validated_data.get('assets')
        assets = []
        
        for asset_data in assets_data:
            # Create asset using the single asset serializer
            serializer = EmployeeAssetSerializer(data=asset_data)
            if serializer.is_valid(raise_exception=True):
                asset = serializer.save()
                assets.append(asset)
        
        return assets

class OffenceDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.CharField(read_only=True)
    
    class Meta:
        model = OffenceDocument
        fields = ['id', 'title', 'file', 'file_url', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

class OffenceSerializer(serializers.ModelSerializer):
    offence_type_display = serializers.CharField(read_only=True)
    documents = OffenceDocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Offence
        fields = [
            'id', 'ref_no', 'entered_on', 'offence_type', 'offence_type_other',
            'total_value', 'details', 'start_date', 'end_date', 'is_cancelled',
            'created_at', 'updated_at', 'offence_type_display', 'documents'
        ]
        read_only_fields = ['id', 'is_cancelled', 'created_at', 'updated_at']

    def validate(self, data):
        if data.get('offence_type') == 'OTHER' and not data.get('offence_type_other'):
            raise serializers.ValidationError({
                'offence_type_other': 'This field is required when offence type is Other.'
            })
        return data
