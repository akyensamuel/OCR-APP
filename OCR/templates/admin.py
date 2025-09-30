from django.contrib import admin
from .models import Template


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'processing_status', 'field_count', 'created_by', 'created_at', 'is_active']
    list_filter = ['processing_status', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'field_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'file', 'is_active')
        }),
        ('Processing', {
            'fields': ('processing_status', 'structure'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Number of Fields')
    def field_count(self, obj):
        return obj.field_count
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
