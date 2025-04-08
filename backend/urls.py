"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
import os
from django.http import FileResponse
from django.views.static import serve

# API documentation setup
schema_view = get_schema_view(
    openapi.Info(
        title="Siargao Tourism API",
        default_version="v1",
        description="API for Siargao Tourism Website",
        contact=openapi.Contact(email="admin@siargao.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

# Custom view to serve media files
def serve_media_file(request, path):
    # First try to serve from media directory
    media_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(media_path) and os.path.isfile(media_path):
        return serve(request, path, document_root=settings.MEDIA_ROOT)
    
    # If not found, try to serve from static/media directory
    static_media_path = os.path.join(settings.STATIC_ROOT, 'media', path)
    if os.path.exists(static_media_path) and os.path.isfile(static_media_path):
        return serve(request, os.path.join('media', path), document_root=settings.STATIC_ROOT)
    
    # If not found, try to serve from staticfiles/media directory
    staticfiles_media_path = os.path.join(settings.STATIC_ROOT, 'media', path)
    if os.path.exists(staticfiles_media_path) and os.path.isfile(staticfiles_media_path):
        return serve(request, os.path.join('media', path), document_root=settings.STATIC_ROOT)
    
    # If all else fails, return 404
    from django.http import Http404
    raise Http404("Media file not found")

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/explore/', include('explore.urls')),
    path('api/events/', include('events.urls')),
    path('api/auth/', include('users.urls')),
    
    # API documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Custom URL pattern to serve media files
    re_path(r'^media/(?P<path>.*)$', serve_media_file, name='serve_media_file'),
]

# Serve media files in development
if settings.DEBUG:
    # First, try to serve from the media directory
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Additional fallback for media files
    media_static_dir = os.path.join(settings.STATIC_ROOT, 'media')
    if os.path.exists(media_static_dir):
        urlpatterns += static('/media/', document_root=media_static_dir)
else:
    # In production, ensure media files are properly served
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
