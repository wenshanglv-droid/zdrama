from rest_framework import serializers
from .models import Production, Performance, Asset, Share

class ProductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Production
        fields = ["id", "title", "genre", "description", "created_at"]

class PerformanceSerializer(serializers.ModelSerializer):
    production_title = serializers.CharField(source="production.title", read_only=True)
    class Meta:
        model = Performance
        fields = ["id", "production", "production_title", "title", "starts_at", "venue", "cast_notes"]

class AssetSerializer(serializers.ModelSerializer):
    performance_title = serializers.CharField(source="performance.title", read_only=True)
    production_title = serializers.CharField(source="performance.production.title", read_only=True)
    class Meta:
        model = Asset
        fields = ["id", "title", "performance", "performance_title", "production_title", "category", "original_name", "size", "sha256", "created_at"]
        read_only_fields = ["original_name", "size", "sha256", "created_at"]

class ShareSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source="recipient.username", read_only=True)
    asset_title = serializers.CharField(source="asset.title", read_only=True)
    class Meta:
        model = Share
        fields = ["id", "asset", "asset_title", "recipient_name", "expires_at", "allow_download", "revoked_at", "created_at"]
