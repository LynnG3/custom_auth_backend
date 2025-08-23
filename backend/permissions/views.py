import logging
from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema

from users.spectacular import CustomJWTAuthenticationScheme
from .models import Role, UserRole, RolePermission
from .serializers import (
    RoleSerializer, UserRoleSerializer,
    RolePermissionSerializer
)
from .decorators import require_admin, require_admin_or_manager

logger = logging.getLogger('permissions')


class RoleViewSet(viewsets.ModelViewSet):
    """ViewSet для управления ролями."""

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=['roles'], summary='Список ролей')
    @require_admin_or_manager()  # Админы и менеджеры могут читать роли
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=['roles'], summary='Детали роли')
    @require_admin_or_manager()  # Админы и менеджеры могут читать роли
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=['roles'], summary='Создание роли')
    @require_admin()  # Только админы могут создавать роли
    def create(self, request, *args, **kwargs):
        try:
            result = super().create(request, *args, **kwargs)
            logger.info(f"Role created successfully: {result.data}")
            return result
        except Exception as e:
            logger.error(f"Error creating role: {e}")
            raise

    @extend_schema(tags=['roles'], summary='Обновление роли')
    @require_admin()  # Только админы могут редактировать роли
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=['roles'], summary='Удаление роли')
    @require_admin()  # Только админы могут удалять роли
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class UserRoleViewSet(viewsets.ModelViewSet):
    """ViewSet для управления ролями пользователей."""

    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=['user-roles'], summary='Список ролей пользователей')
    def list(self, request, *args, **kwargs):
        # Все аутентифицированные могут читать роли пользователей
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=['user-roles'], summary='Детали роли пользователя')
    def retrieve(self, request, *args, **kwargs):
        # Все аутентифицированные могут читать роли пользователей
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=['user-roles'], summary='Назначение роли')
    @require_admin()  # Только админы могут назначать роли
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(tags=['user-roles'], summary='Обновление роли')
    @require_admin()  # Только админы могут обновлять роли
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(tags=['user-roles'], summary='Частичное обновление роли')
    @require_admin()  # Только админы могут обновлять роли
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(tags=['user-roles'], summary='Удаление роли')
    @require_admin()  # Только админы могут удалять роли
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class RolePermissionViewSet(viewsets.ModelViewSet):
    """ViewSet для управления разрешениями ролей."""

    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=['permissions'], summary='Список разрешений')
    @require_admin_or_manager()  # Админы и менеджеры могут читать
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=['permissions'], summary='Детали разрешения')
    @require_admin_or_manager()  # Админы и менеджеры могут читать
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

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
