import logging
from rest_framework import serializers
from .models import Role, UserRole, RolePermission, ResourceType


logger = logging.getLogger(__name__)


class ResourceTypeSerializer(serializers.ModelSerializer):
    """Сериализатор для типов ресурсов."""
    
    class Meta:
        model = ResourceType
        fields = [
            'id', 'name',
            'description', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RoleSerializer(serializers.ModelSerializer):
    """Сериализатор для ролей."""
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'description',
            'is_default', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RoleDetailSerializer(RoleSerializer):
    """Детальный сериализатор для ролей."""
    
    permissions = serializers.SerializerMethodField()
    
    class Meta(RoleSerializer.Meta):
        fields = RoleSerializer.Meta.fields + ['permissions']
    
    def get_permissions(self, obj):
        """Получает разрешения роли."""
        permissions = RolePermission.objects.filter(
            role=obj
        ).select_related('resource_type')
        return RolePermissionSerializer(permissions, many=True).data


class UserRoleSerializer(serializers.ModelSerializer):
    """Сериализатор для связи пользователей с ролями."""

    role_name = serializers.CharField(source='role.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = UserRole
        fields = [
            'id', 'user', 'role', 'role_name',
            'user_email', 'assigned_by', 'assigned_at', 'is_active'
        ]
        read_only_fields = ['id', 'assigned_at']


class RolePermissionSerializer(serializers.ModelSerializer):
    """Сериализатор для разрешений ролей."""

    resource_type_name = serializers.CharField(
        source='resource_type.name',
        read_only=True
    )

    class Meta:
        model = RolePermission
        fields = [
            'id', 'role', 'resource_type', 'resource_type_name',
            'can_create', 'can_read', 'can_update', 'can_delete',
            'can_manage_others', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RolePermissionDetailSerializer(RolePermissionSerializer):
    """Детальный сериализатор для разрешений ролей."""
    
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    class Meta(RolePermissionSerializer.Meta):
        fields = RolePermissionSerializer.Meta.fields + ['role_name']


class RolePermissionUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления разрешений ролей."""

    class Meta:
        model = RolePermission
        fields = [
            'can_create', 'can_read', 'can_update', 'can_delete',
            'can_manage_others'
        ]

    def validate(self, attrs):
        """Валидация логики наследования прав."""
        if attrs.get('can_manage_others'):
            # Если можно управлять чужими, то должны быть базовые права
            if not attrs.get('can_read', False):
                attrs['can_read'] = True
            if not attrs.get('can_update', False) and not data.get('can_delete', False):
                # Должно быть хотя бы одно право на управление
                attrs['can_update'] = True

        return attrs
