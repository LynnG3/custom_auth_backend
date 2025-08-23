from django.contrib import admin
from .models import Role, UserRole, RolePermission


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Админка для управления ролями."""
    
    list_display = [
        'name', 'description_short', 'is_default', 'user_count', 'created_at'
    ]
    list_filter = ['is_default', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    
    def description_short(self, obj):
        """Короткое описание роли."""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Описание'
    
    def user_count(self, obj):
        """Количество пользователей с этой ролью."""
        count = UserRole.objects.filter(role=obj, is_active=True).count()
        return count
    user_count.short_description = 'Пользователей'


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Админка для управления ролями пользователей."""
    
    list_display = [
        'user_email', 'role_name', 'assigned_by_email', 'is_active', 'assigned_at'
    ]
    list_filter = ['role__name', 'is_active', 'assigned_at']
    search_fields = ['user__email', 'role__name', 'assigned_by__email']
    readonly_fields = ['assigned_at']
    
    def user_email(self, obj):
        """Email пользователя."""
        return obj.user.email
    user_email.short_description = 'Пользователь'
    
    def role_name(self, obj):
        """Название роли."""
        return obj.role.get_name_display()
    role_name.short_description = 'Роль'
    
    def assigned_by_email(self, obj):
        """Email назначившего роль."""
        return obj.assigned_by.email if obj.assigned_by else '-'
    assigned_by_email.short_description = 'Назначил'


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    """Админка для управления разрешениями ролей."""
    
    list_display = [
        'role_name', 'resource_type_display', 'permissions_summary', 'created_at'
    ]
    list_filter = ['role__name', 'resource_type', 'created_at']
    search_fields = ['role__name', 'resource_type']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('role', 'resource_type')
        }),
        ('Права доступа', {
            'fields': (
                'can_create', 'can_read', 'can_update', 'can_delete', 'can_manage_others'
            ),
            'description': 'Настройте права доступа для данной роли на данный тип ресурса'
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def role_name(self, obj):
        """Название роли."""
        return obj.role.get_name_display()
    role_name.short_description = 'Роль'
    
    def resource_type_display(self, obj):
        """Отображаемое название типа ресурса."""
        return obj.get_resource_type_display()
    resource_type_display.short_description = 'Тип ресурса'
    
    def permissions_summary(self, obj):
        """Сводка по правам."""
        permissions = []
        if obj.can_create:
            permissions.append('Создание')
        if obj.can_read:
            permissions.append('Чтение')
        if obj.can_update:
            permissions.append('Обновление')
        if obj.can_delete:
            permissions.append('Удаление')
        if obj.can_manage_others:
            permissions.append('Управление чужими')
        
        if permissions:
            return ', '.join(permissions)
        return 'Нет прав'
    permissions_summary.short_description = 'Права'


# Настройки админки
admin.site.site_header = 'Система управления разрешениями'
admin.site.site_title = 'Админка разрешений'
admin.site.index_title = 'Управление ролями и разрешениями'


