from rest_framework import serializers

class CreateCheckoutRequestSerializer(serializers.Serializer):
    
    currency = serializers.CharField(required=False)
    success_url = serializers.URLField(required=False)
    cancel_url = serializers.URLField(required=False)

class CreatedSessionSerializer(serializers.Serializer):
    vendor_id = serializers.CharField()
    order_id = serializers.IntegerField()
    session_id = serializers.CharField()
    redirect_url = serializers.URLField()

class CreateCheckoutResponseSerializer(serializers.Serializer):
    sessions = CreatedSessionSerializer(many=True)
