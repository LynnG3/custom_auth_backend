from rest_framework import serializers

from permissions.utils import can_user_access_resource
from .models import Resource


class ResourceSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Resource."""

    owner_email = serializers.CharField(source='owner.email', read_only=True)

    class Meta:
        model = Resource
        fields = [
            'id', 'name', 'resource_type', 
            'owner', 'owner_email', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner_email']

    def validate(self, attrs):
        """Валидация данных."""
        # Проверяем, что пользователь может создавать ресурсы данного типа
        user = self.context['request'].user
        resource_type = attrs.get('resource_type')

        if not can_user_access_resource(user, resource_type, 'create'):
            raise serializers.ValidationError(
                f"У вас нет прав на создание ресурсов типа '{resource_type}'"
            )

        return attrs
