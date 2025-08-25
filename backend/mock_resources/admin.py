from django.contrib import admin
from .models import Resource
from permissions.models import ResourceType


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    """Админка для ресурсов."""
    
    list_display = [
        'name', 'owner', 'created_at', 'updated_at'
    ]
    list_filter = [
        'resource_type', 'created_at', 'updated_at'
    ]
    search_fields = [
        'name', 'resource_type__name', 'owner__email'
    ]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'resource_type')
        }),
        ('Владелец', {
            'fields': ('owner',)
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    
    def get_queryset(self, request):
        """Оптимизируем запросы."""
        return super().get_queryset(request).select_related('resource_type', 'owner')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Фильтруем только активные типы ресурсов."""
        if db_field.name == "resource_type":
            kwargs["queryset"] = ResourceType.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
