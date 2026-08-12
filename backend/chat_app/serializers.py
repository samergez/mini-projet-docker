from rest_framework import serializers

class ChatSerializer(serializers.Serializer):
    prompt = serializers.CharField(required=True)
    metadata_filters = serializers.JSONField(required=False, default=dict)
    history = serializers.ListField(
        child=serializers.DictField(), required=False, default=list
    )
    model_name = serializers.CharField(required=False, default="llama-3.1-8b-instant")