from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, DestinationViewSet, ActivityViewSet, CultureViewSet, FavoriteViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'destinations', DestinationViewSet)
router.register(r'activities', ActivityViewSet)
router.register(r'cultures', CultureViewSet)
router.register(r'favorites', FavoriteViewSet, basename='favorite')

urlpatterns = [
    path('', include(router.urls)),
]
