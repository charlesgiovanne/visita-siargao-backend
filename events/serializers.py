from rest_framework import serializers
from .models import Event

class EventSerializer(serializers.ModelSerializer):
    month_name = serializers.CharField(source='month', read_only=True)
    
    class Meta:
        model = Event
        fields = ['id', 'title', 'image', 'description', 'date', 'month_name', 'created_at', 'updated_at']
        read_only_fields = ['month']
