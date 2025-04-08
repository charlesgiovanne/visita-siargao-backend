from django.contrib import admin
from .models import Category, Destination, Activity, Culture

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ('title', 'location_name', 'created_at')
    list_filter = ('categories',)
    search_fields = ('title', 'short_description', 'location_name')
    filter_horizontal = ('categories',)

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'duration', 'created_at')
    search_fields = ('title', 'short_description', 'duration')

@admin.register(Culture)
class CultureAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title', 'short_description')
