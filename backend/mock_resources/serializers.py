from rest_framework import serializers

from permissions.models import ResourceType
from permissions.utils import can_user_access_resource
from .models import Resource


class ResourceSerializer(serializers.ModelSerializer):
    """Сериализатор для ресурсов."""
    
    resource_type_name = serializers.CharField(
        source='resource_type.name', 
        read_only=True,
        help_text='Название типа ресурса'
    )

    owner_email = serializers.CharField(
        source='owner.email', 
        read_only=True,
        help_text='Email владельца'
    )
    
    class Meta:
        model = Resource
        fields = [
            'id', 'name', 'resource_type', 'resource_type_name', 'owner', 'owner_email', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']
    
    def validate_resource_type(self, value):
        """Валидация: тип ресурса должен быть активным."""
        if not value.is_active:
            raise serializers.ValidationError(
                f"Тип ресурса '{value.name}' неактивен"
            )
        return value
    
    def validate(self, data):
        """Валидация прав доступа."""
        user = self.context['request'].user
        resource_type = data.get('resource_type')
        
        if resource_type:
            # Проверяем права на создание ресурса данного типа
            if not can_user_access_resource(user, resource_type, 'create'):
                raise serializers.ValidationError(
                    f"Недостаточно прав для создания ресурса типа '{resource_type.name}'"
                )
        
        return data


class ResourceCreateSerializer(ResourceSerializer):
    """Сериализатор для создания ресурсов."""

    class Meta(ResourceSerializer.Meta):
        fields = ['name', 'resource_type']

    def create(self, validated_data):
        """Автоматически устанавливаем владельца."""
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class ResourceUpdateSerializer(ResourceSerializer):
    """Сериализатор для обновления ресурсов."""

    class Meta(ResourceSerializer.Meta):
        fields = ['name', 'resource_type']
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']


class ResourceTypeSerializer(serializers.ModelSerializer):
    """Сериализатор для типов ресурсов в контексте ресурсов."""

    resources_count = serializers.SerializerMethodField()

    class Meta:
        model = ResourceType
        fields = ['id', 'name', 'description', 'resources_count']

    def get_resources_count(self, obj):
        """Возвращает количество ресурсов данного типа."""
        return obj.resources.count()
