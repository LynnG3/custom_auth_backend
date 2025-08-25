from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action

from users.spectacular import CustomJWTAuthenticationScheme
from permissions.decorators import (
    require_user_or_higher,
    require_dynamic_permission
)
from permissions.models import ResourceType
from .models import Resource
from .serializers import (
    ResourceSerializer, ResourceCreateSerializer, 
    ResourceUpdateSerializer, ResourceTypeSerializer
)


class ResourceViewSet(viewsets.ModelViewSet):
    """ViewSet для управления ресурсами с динамическими типами."""

    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'resource_type__name']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Выбираем сериализатор в зависимости от действия."""
        if self.action == 'create':
            return ResourceCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ResourceUpdateSerializer
        return ResourceSerializer

    def get_permissions(self):
        """Динамически устанавливаем права доступа."""
        if self.action == 'list' and not self.request.user.is_authenticated:
            # Гости могут читать список ресурсов без аутентификации
            return []
        return super().get_permissions()

    def get_queryset(self):
        """Фильтруем ресурсы в зависимости от роли пользователя."""
        queryset = super().get_queryset().select_related('resource_type', 'owner')

        if not self.request.user.is_authenticated:
            # Гости видят только активные ресурсы
            return queryset.filter(resource_type__is_active=True)
        
        # Для аутентифицированных пользователей применяем декораторы
        return queryset

    @extend_schema(tags=['resources'], summary='Список ресурсов')
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=['resources'], summary='Детали ресурса')
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=['resources'], summary='Создание ресурса')
    @require_user_or_higher()
    @require_dynamic_permission('create')
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=['resources'], summary='Обновление ресурса')
    @require_user_or_higher()
    @require_dynamic_permission('update')
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=['resources'], summary='Удаление ресурса')
    @require_user_or_higher()
    @require_dynamic_permission('delete')
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(tags=['resources'], summary='Частичное обновление ресурса')
    @require_user_or_higher()
    @require_dynamic_permission('update')
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        tags=['resources'], 
        summary='Получение доступных типов ресурсов',
        description='Возвращает список активных типов ресурсов для создания'
    )
    @action(detail=False, methods=['get'])
    def available_types(self, request):
        """Получение доступных типов ресурсов для создания."""
        user = request.user
        available_types = []
        
        for resource_type in ResourceType.objects.filter(is_active=True):
            if can_user_access_resource(user, resource_type, 'create'):
                available_types.append(resource_type)
        
        serializer = ResourceTypeSerializer(available_types, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['resources'], 
        summary='Статистика ресурсов по типам',
        description='Возвращает количество ресурсов по типам'
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Статистика ресурсов по типам."""
        from django.db.models import Count
        
        stats = Resource.objects.values('resource_type__name').annotate(
            count=Count('id')
        ).order_by('resource_type__name')
        
        return Response(stats)

    @extend_schema(
        tags=['resources'], 
        summary='Ресурсы пользователя',
        description='Возвращает ресурсы, принадлежащие текущему пользователю'
    )
    @action(detail=False, methods=['get'])
    def my_resources(self, request):
        """Ресурсы текущего пользователя."""
        queryset = self.get_queryset().filter(owner=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
