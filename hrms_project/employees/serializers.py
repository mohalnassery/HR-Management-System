from rest_framework import serializers
from .models import EmployeeAsset, AssetType, EmployeeOffence, OffenseDocument, OffenseRule
from django.utils import timezone

class AssetTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetType
        fields = '__all__'

class EmployeeAssetSerializer(serializers.ModelSerializer):
    asset_type_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = EmployeeAsset
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['asset_type_display'] = instance.get_asset_type_display()
        return representation

class BulkEmployeeAssetSerializer(serializers.Serializer):
    employee_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )
    asset_type = serializers.PrimaryKeyRelatedField(
        queryset=AssetType.objects.all(),
        required=True
    )
    asset_number = serializers.CharField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    issue_date = serializers.DateField(required=True)
    return_date = serializers.DateField(required=False, allow_null=True)
    
    def create(self, validated_data):
        employee_ids = validated_data.pop('employee_ids')
        assets = []
        
        for employee_id in employee_ids:
            asset = EmployeeAsset.objects.create(
                employee_id=employee_id,
                **validated_data
            )
            assets.append(asset)
        
        return assets

class OffenseDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OffenseDocument
        fields = '__all__'

class OffenseRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = OffenseRule
        fields = '__all__'

class EmployeeOffenceSerializer(serializers.ModelSerializer):
    original_penalty_display = serializers.SerializerMethodField()
    applied_penalty_display = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeOffence
        fields = '__all__'
        read_only_fields = ('created_by', 'modified_by', 'created_at', 'updated_at')

    def create(self, validated_data):
        # Set original_penalty to match applied_penalty if not provided
        if 'original_penalty' not in validated_data:
            validated_data['original_penalty'] = validated_data.get('applied_penalty')
        
        # Set details to empty string if not provided
        if 'details' not in validated_data:
            validated_data['details'] = ''
            
        # Ensure is_active is set to True for new offenses
        if 'is_active' not in validated_data:
            validated_data['is_active'] = True
            
        return super().create(validated_data)
    
    def to_representation(self, instance):
        """Enhance the serialized representation with additional fields and ensure proper active status"""
        representation = super().to_representation(instance)
        
        # Ensure newly created offenses are shown as active
        created_recently = False
        if instance.created_at:
            # Consider offenses created in the last hour as "recent"
            created_recently = (timezone.now() - instance.created_at).total_seconds() < 3600
            
        # If offense was created recently, ensure it's displayed as active
        if created_recently:
            representation['is_active'] = True
            
        # Include rule details if available
        if instance.rule:
            representation['rule'] = {
                'id': instance.rule.id,
                'rule_id': instance.rule.rule_id,
                'name': instance.rule.name,
                'description': instance.rule.description,
                'group': instance.rule.group,
                'group_display': instance.rule.get_group_display()
            }
            
        return representation
    
    def get_original_penalty_display(self, obj):
        """Get the human-readable display for original_penalty"""
        return obj.get_original_penalty_display()
    
    def get_applied_penalty_display(self, obj):
        """Get the human-readable display for applied_penalty"""
        return obj.get_applied_penalty_display()
