from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Event
from .serializers import EventSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from datetime import datetime

# Create your views here.

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().order_by('-date')
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = Event.objects.all().order_by('-date')
        
        month = self.request.query_params.get('month')
        if month:
            try:
                # Get events for the specified month
                month_number = int(month)
                current_year = timezone.now().year
                
                # Filter events by month
                queryset = queryset.filter(date__year=current_year, date__month=month_number)
            except ValueError:
                pass  # Invalid month parameter, return all events
        
        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def by_month(self, request):
        month = request.query_params.get('month')
        if month:
            events = Event.objects.filter(month__iexact=month).order_by('date')
            serializer = self.get_serializer(events, many=True)
            return Response(serializer.data)
        return Response({'error': 'Month parameter is required'}, status=400)
