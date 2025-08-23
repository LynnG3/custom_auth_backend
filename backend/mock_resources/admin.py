from django.contrib import admin

from .models import Resource

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    """Админка для управления ресурсами."""

    list_display = [
        'name', 'resource_type_display', 'owner_email', 'created_at', 'updated_at'
    ]
    list_filter = ['resource_type', 'created_at', 'updated_at']
    search_fields = ['name', 'owner__email']
    readonly_fields = ['created_at', 'updated_at']

    def resource_type_display(self, obj):
        """Отображаемое название типа ресурса."""
        return obj.get_resource_type_display()
    resource_type_display.short_description = 'Тип ресурса'

    def owner_email(self, obj):
        """Email владельца ресурса."""
        return obj.owner.email if obj.owner else '-'
    owner_email.short_description = 'Владелец'
