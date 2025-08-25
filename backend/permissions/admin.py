from django.contrib import admin
from .models import Role, UserRole, RolePermission, ResourceType


@admin.register(ResourceType)
class ResourceTypeAdmin(admin.ModelAdmin):
    """Админка для типов ресурсов."""
    
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    ordering = ['name']

    actions = ['activate_resources', 'deactivate_resources']

    def activate_resources(self, request, queryset):
        """Активировать выбранные ресурсы."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, 
            f'Успешно активировано {updated} ресурсов.'
        )
    activate_resources.short_description = "Активировать выбранные ресурсы"

    def deactivate_resources(self, request, queryset):
        """Деактивировать выбранные ресурсы."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'Успешно деактивировано {updated} ресурсов.'
        )
    deactivate_resources.short_description = "Деактивировать выбранные ресурсы"


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Админка для ролей."""

    list_display = ['name', 'description', 'is_default', 'created_at']
    list_filter = ['is_default', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    ordering = ['name']


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Админка для связи пользователей с ролями."""

    list_display = ['user', 'role', 'assigned_by', 'assigned_at', 'is_active']
    list_filter = ['role', 'is_active', 'assigned_at']
    search_fields = ['user__email', 'role__name']
    readonly_fields = ['assigned_at']
    ordering = ['-assigned_at']


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    """Админка для разрешений ролей."""

    list_display = [
        'role', 'resource_type', 'can_create', 'can_read',
        'can_update', 'can_delete', 'can_manage_others', 'created_at'
    ]
    list_filter = [
        'role', 'resource_type', 'can_create', 'can_read',
        'can_update', 'can_delete', 'can_manage_others', 'created_at'
    ]
    search_fields = ['role__name', 'resource_type__name']
    readonly_fields = ['created_at']
    ordering = ['role__name', 'resource_type__name']

    fieldsets = (
        ('Основная информация', {
            'fields': ('role', 'resource_type')
        }),
        ('Права доступа', {
            'fields': (
                'can_create', 'can_read', 'can_update', 'can_delete',
                'can_manage_others'
            )
        }),
        ('Метаданные', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


admin.site.site_header = 'Система управления разрешениями'
admin.site.site_title = 'Админка разрешений'
admin.site.index_title = 'Управление ролями и разрешениями'
