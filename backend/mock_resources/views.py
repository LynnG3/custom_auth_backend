from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from permissions.decorators import (
    require_user_or_higher,
    require_resource_permission
)
from .models import Resource
from .serializers import ResourceSerializer


class ResourceViewSet(viewsets.ModelViewSet):
    """ViewSet для управления ресурсами."""

    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """Динамически устанавливаем права доступа."""
        if self.action == 'list' and not self.request.user.is_authenticated:
            # Гости могут читать список ресурсов без аутентификации
            return []
        return super().get_permissions()

    def get_queryset(self):
        """Фильтруем ресурсы в зависимости от роли пользователя."""
        queryset = super().get_queryset()

        if not self.request.user.is_authenticated:
            # Гости видят только продукты
            return queryset.filter(resource_type='product')
        # Для аутентифицированных пользователей применяем декораторы
        return queryset

    @extend_schema(tags=['resources'], summary='Список ресурсов')
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=['resources'], summary='Детали ресурса')
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=['resources'], summary='Создание ресурса')
    @require_user_or_higher()  # Пользователи и выше могут создавать
    @require_resource_permission('product', 'create')  # Проверяем права на ресурс
    def create(self, request, *args, **kwargs):
        # Автоматически устанавливаем владельца
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(tags=['resources'], summary='Обновление ресурса')
    @require_user_or_higher()
    @require_resource_permission('product', 'update')
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=['resources'], summary='Удаление ресурса')
    @require_user_or_higher()
    @require_resource_permission('product', 'delete')
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(tags=['resources'], summary='Частичное обновление ресурса')
    @require_user_or_higher()
    @require_resource_permission('product', 'update')
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
