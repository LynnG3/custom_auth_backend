import logging
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from drf_spectacular.utils import extend_schema

from users.spectacular import CustomJWTAuthenticationScheme
from .models import Role, UserRole, RolePermission, ResourceType
from .serializers import (
    RoleSerializer, RoleDetailSerializer, UserRoleSerializer,
    RolePermissionSerializer, RolePermissionDetailSerializer,
    RolePermissionUpdateSerializer, ResourceTypeSerializer
)
from .decorators import require_admin


logger = logging.getLogger('permissions')


class ResourceTypeViewSet(viewsets.ModelViewSet):
    """API для управления типами ресурсов."""

    queryset = ResourceType.objects.filter(is_active=True)
    serializer_class = ResourceTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Фильтруем только активные ресурсы."""
        return ResourceType.objects.filter(is_active=True)

    @require_admin()
    def create(self, request, *args, **kwargs):
        """Создание нового типа ресурса."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            resource_type = serializer.save()

            # Автоматически создаем разрешения для админа
            for role in Role.objects.all():
                RolePermission.objects.update_or_create(
                    role=role,
                    resource_type=resource_type,
                    defaults={
                        'can_read': True,
                        'can_create': role.name == 'admin',
                        'can_update': role.name == 'admin',
                        'can_delete': role.name == 'admin',
                        'can_manage_others': role.name == 'admin'
                    }
                )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @require_admin()
    def update(self, request, *args, **kwargs):
        """Обновление типа ресурса."""
        return super().update(request, *args, **kwargs)

    @require_admin()
    def destroy(self, request, *args, **kwargs):
        """Мягкое удаление типа ресурса."""
        resource_type = self.get_object()
        resource_type.is_active = False
        resource_type.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    @require_admin()
    def activate(self, request, pk=None):
        """Активация типа ресурса."""
        resource_type = self.get_object()
        resource_type.is_active = True
        resource_type.save()
        return Response({'status': 'Resource type activated'})

    @action(detail=True, methods=['post'])
    @require_admin()
    def deactivate(self, request, pk=None):
        """Деактивация типа ресурса."""
        resource_type = self.get_object()
        resource_type.is_active = False
        resource_type.save()
        return Response({'status': 'Resource type deactivated'})


class RoleViewSet(viewsets.ModelViewSet):
    """API для управления ролями."""

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RoleDetailSerializer
        return RoleSerializer

    @require_admin()
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @require_admin()
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @require_admin()
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class UserRoleViewSet(viewsets.ModelViewSet):
    """API для управления ролями пользователей."""

    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    @require_admin()
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @require_admin()
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @require_admin()
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class RolePermissionViewSet(viewsets.ModelViewSet):
    """API для управления разрешениями ролей."""

    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['retrieve', 'list']:
            return RolePermissionDetailSerializer
        elif self.action in ['update', 'partial_update']:
            return RolePermissionUpdateSerializer
        return RolePermissionSerializer

    @extend_schema(tags=['permissions'], summary='Создание разрешения')
    @require_admin()
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=['permissions'], summary='Обновление разрешения')
    @require_admin()
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=['permissions'], summary='Частичное обновление разрешения')
    @require_admin()  # Только админы могут обновлять
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=['permissions'], summary='Удаление разрешения')
    @require_admin()
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def by_role(self, request):
        """Получение разрешений по роли."""
        role_id = request.query_params.get('role_id')
        if not role_id:
            return Response(
                {'error': 'role_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        role_permissions = RolePermission.objects.filter(role_id=role_id)
        serializer = self.get_serializer(role_permissions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_resource(self, request):
        """Получение разрешений по типу ресурса."""
        resource_type_id = request.query_params.get('resource_type_id')
        if not resource_type_id:
            return Response(
                {'error': 'resource_type_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        role_permissions = RolePermission.objects.filter(
            resource_type_id=resource_type_id
        )
        serializer = self.get_serializer(role_permissions, many=True)
        return Response(serializer.data)
