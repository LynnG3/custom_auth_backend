import logging
from rest_framework import serializers
from .models import Role, UserRole, RolePermission


logger = logging.getLogger(__name__)


class RoleSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Role."""

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'is_default', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        """Валидация данных."""
        name = attrs.get('name')
        if name:
            # Проверяем, что имя не является зарезервированным
            reserved_names = ['admin', 'manager', 'user', 'guest']
            if name in reserved_names:
                logger.warning(f"Attempted to create reserved role: {name}")
                raise serializers.ValidationError(
                    f"Имя '{name}' зарезервировано системой"
                )

            # Проверяем уникальность
            if Role.objects.filter(name=name).exists():
                logger.warning(f"Role with name '{name}' already exists")
                raise serializers.ValidationError(
                    f"Роль с именем '{name}' уже существует"
                )

        return attrs


class RoleDetailSerializer(serializers.ModelSerializer):
    """Сериализатор деталей модели Role."""

    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            'id', 'name', 'description',
            'is_default', 'created_at', 'user_count'
        ]
        read_only_fields = ['id', 'created_at', 'user_count']

    def get_user_count(self, obj):
        """Количество пользователей с этой ролью."""
        return UserRole.objects.filter(role=obj, is_active=True).count()


class UserRoleSerializer(serializers.ModelSerializer):
    """Сериализатор для модели UserRole."""

    class Meta:
        model = UserRole
        fields = [
            'id', 'user', 'role',
            'assigned_by', 'assigned_at', 'is_active'
        ]
        read_only_fields = ['id', 'assigned_at']


class UserRoleDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор для модели UserRole."""

    user_email = serializers.CharField(source='user.email', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    role_name = serializers.CharField(source='role.name', read_only=True)
    role_description = serializers.CharField(
        source='role.description', read_only=True
    )
    assigned_by_email = serializers.CharField(
        source='assigned_by.email', read_only=True
    )

    class Meta:
        model = UserRole
        fields = [
            'id', 'user', 'user_email', 'user_full_name',
            'role', 'role_name', 'role_description',
            'assigned_by', 'assigned_by_email', 'assigned_at', 'is_active'
        ]
        read_only_fields = ['id', 'assigned_at']

    def get_user_full_name(self, obj):
        """Полное имя пользователя."""
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.last_name} {obj.user.first_name}"
        return obj.user.email


class RolePermissionSerializer(serializers.ModelSerializer):
    """Сериализатор для модели RolePermission."""

    role_name = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = RolePermission
        fields = [
            'id', 'role', 'role_name', 'resource_type',
            'can_create', 'can_read', 'can_update', 'can_delete',
            'can_manage_others',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        """Валидация данных."""
        if attrs.get('can_manage_others'):
            if not attrs.get('can_read'):
                raise serializers.ValidationError(
                    "Если можно управлять чужими ресурсами, "
                    "то должно быть право на чтение"
                )
            if not attrs.get('can_update') and not attrs.get('can_delete'):
                raise serializers.ValidationError(
                    "Если можно управлять чужими ресурсами, "
                    "то должны быть права на обновление или удаление"
                )

        return attrs
