from django.contrib import admin
from .models import Event

# Register your models here.
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'month')
    list_filter = ('month',)
    search_fields = ('title', 'description')
    readonly_fields = ('month',)
