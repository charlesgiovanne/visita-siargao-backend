from rest_framework import serializers
from .models import Category, Destination, Activity, Culture, Favorite

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class DestinationSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        many=True,
        write_only=True,
        source='categories',
        required=False
    )
    is_favorite = serializers.SerializerMethodField()
    
    class Meta:
        model = Destination
        fields = ['id', 'title', 'image', 'categories', 'category_ids', 'short_description', 
                  'long_description', 'location_name', 'maps_link', 'created_at', 'updated_at', 'is_favorite']
    
    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, destination=obj).exists()
        return False

class ActivitySerializer(serializers.ModelSerializer):
    is_favorite = serializers.SerializerMethodField()
    
    class Meta:
        model = Activity
        fields = ['id', 'title', 'image', 'short_description', 'long_description', 
                  'tips', 'duration', 'created_at', 'updated_at', 'is_favorite']
    
    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, activity=obj).exists()
        return False

class CultureSerializer(serializers.ModelSerializer):
    is_favorite = serializers.SerializerMethodField()
    
    class Meta:
        model = Culture
        fields = ['id', 'title', 'image', 'short_description', 'long_description', 
                  'created_at', 'updated_at', 'is_favorite']
    
    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, culture=obj).exists()
        return False

class FavoriteSerializer(serializers.ModelSerializer):
    destination_details = DestinationSerializer(source='destination', read_only=True)
    activity_details = ActivitySerializer(source='activity', read_only=True)
    culture_details = CultureSerializer(source='culture', read_only=True)
    
    class Meta:
        model = Favorite
        fields = ['id', 'user', 'destination', 'activity', 'culture', 'created_at',
                 'destination_details', 'activity_details', 'culture_details']
        read_only_fields = ['user']
    
    def validate(self, data):
        # Ensure at least one item type is provided
        if not any(data.get(field) for field in ['destination', 'activity', 'culture']):
            raise serializers.ValidationError("At least one of destination, activity, or culture must be provided.")
        return data
