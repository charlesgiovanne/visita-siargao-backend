from django.shortcuts import render
from rest_framework import viewsets, generics, permissions
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Category, Destination, Activity, Culture, Favorite
from .serializers import CategorySerializer, DestinationSerializer, ActivitySerializer, CultureSerializer, FavoriteSerializer
from django.db.models import Q
from django.conf import settings

# Create your views here.

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()

class DestinationViewSet(viewsets.ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        category_id = request.query_params.get('category_id')
        if category_id:
            destinations = Destination.objects.filter(categories__id=category_id)
            serializer = self.get_serializer(destinations, many=True)
            return Response(serializer.data)
        return Response({'error': 'Category ID is required'}, status=400)
    
    def get_queryset(self):
        queryset = Destination.objects.all()
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(short_description__icontains=search_query) |
                Q(long_description__icontains=search_query)
            )
        return queryset

class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def get_queryset(self):
        queryset = Activity.objects.all()
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(short_description__icontains=search_query) |
                Q(long_description__icontains=search_query) |
                Q(tips__icontains=search_query)
            )
        return queryset

class CultureViewSet(viewsets.ModelViewSet):
    queryset = Culture.objects.all()
    serializer_class = CultureSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def get_queryset(self):
        queryset = Culture.objects.all()
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(short_description__icontains=search_query) |
                Q(long_description__icontains=search_query)
            )
        return queryset

class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def toggle(self, request):
        item_type = request.data.get('item_type')
        item_id = request.data.get('item_id')
        
        if not item_type or not item_id:
            return Response(
                {"error": "Both item_type and item_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate item_type
        if item_type not in ['destination', 'activity', 'culture']:
            return Response(
                {"error": "item_type must be one of: destination, activity, culture"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the item exists
        try:
            if item_type == 'destination':
                item = Destination.objects.get(id=item_id)
                existing = Favorite.objects.filter(user=request.user, destination=item).first()
                if existing:
                    existing.delete()
                    return Response({"status": "removed"}, status=status.HTTP_200_OK)
                else:
                    Favorite.objects.create(user=request.user, destination=item)
                    return Response({"status": "added"}, status=status.HTTP_201_CREATED)
            
            elif item_type == 'activity':
                item = Activity.objects.get(id=item_id)
                existing = Favorite.objects.filter(user=request.user, activity=item).first()
                if existing:
                    existing.delete()
                    return Response({"status": "removed"}, status=status.HTTP_200_OK)
                else:
                    Favorite.objects.create(user=request.user, activity=item)
                    return Response({"status": "added"}, status=status.HTTP_201_CREATED)
            
            elif item_type == 'culture':
                item = Culture.objects.get(id=item_id)
                existing = Favorite.objects.filter(user=request.user, culture=item).first()
                if existing:
                    existing.delete()
                    return Response({"status": "removed"}, status=status.HTTP_200_OK)
                else:
                    Favorite.objects.create(user=request.user, culture=item)
                    return Response({"status": "added"}, status=status.HTTP_201_CREATED)
        
        except (Destination.DoesNotExist, Activity.DoesNotExist, Culture.DoesNotExist):
            return Response(
                {"error": f"{item_type} with id {item_id} does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )
