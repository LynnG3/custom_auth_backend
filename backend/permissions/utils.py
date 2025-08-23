from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import status
from functools import wraps
from .models import UserRole, RolePermission
import logging

logger = logging.getLogger(__name__)


def get_user_role(user):
    """Получает роль пользователя (самую приоритетную)."""
    if not user.is_authenticated:
        return None
    
    # Кэшируем роль пользователя на 5 минут
    cache_key = f'user_role_{user.id}'
    cached_role = cache.get(cache_key)
    
    if cached_role is not None:
        return cached_role
    
    # Получаем самую приоритетную роль пользователя
    user_role = UserRole.objects.filter(
        user=user,
        is_active=True
    ).select_related('role').order_by('role__name').first()
    
    if user_role:
        role_name = user_role.role.name
        cache.set(cache_key, role_name, 300)  # 5 минут
        return role_name
    
    return None


def user_has_role(user, role_name):
    """Проверяет, есть ли у пользователя конкретная роль."""
    user_role = get_user_role(user)
    return user_role == role_name


def user_is_admin(user):
    """Проверяет, является ли пользователь администратором."""
    return user_has_role(user, 'admin')


def user_is_manager(user):
    """Проверяет, является ли пользователь менеджером."""
    return user_has_role(user, 'manager')


def user_is_user(user):
    """Проверяет, является ли пользователь обычным пользователем."""
    return user_has_role(user, 'user')


def get_role_permissions(role_name, resource_type):
    """Получает разрешения роли на конкретный тип ресурса."""
    try:
        permission = RolePermission.objects.get(role__name=role_name, resource_type=resource_type)
        return permission
    except RolePermission.DoesNotExist:
        return None


def can_user_access_resource(user, resource_type, action, resource_owner=None):
    """
    Проверяет, может ли пользователь выполнить действие с ресурсом.
    
    Args:
        user: Пользователь
        resource_type: Тип ресурса ('product', 'order', 'user')
        action: Действие ('create', 'read', 'update', 'delete')
        resource_owner: Владелец ресурса (для проверки своих/чужих)
    """
    if not user.is_authenticated:
        # Гости могут только читать продукты
        if resource_type == 'product' and action == 'read':
            return True
        return False
    
    user_role = get_user_role(user)
    logger.debug(f"User {user.email} has role: {user_role}")
    
    if not user_role:
        logger.warning(f"User {user.email} has no role assigned")
        return False
    
    permission = get_role_permissions(user_role, resource_type)
    logger.debug(f"Permission for role {user_role} on {resource_type}: {permission}")
    
    if not permission:
        logger.warning(f"No permission found for role {user_role} on {resource_type}")
        return False
    
    # Проверяем действие
    if action == 'create':
        result = permission.can_create
        logger.debug(f"Can create: {result}")
        return result
    elif action == 'read':
        result = permission.can_read
        logger.debug(f"Can read: {result}")
        return result
    elif action == 'update':
        if permission.can_manage_others:
            result = permission.can_update
            logger.debug(f"Can update (manage others): {result}")
            return result
        elif permission.can_update and resource_owner:
            result = str(user.id) == str(resource_owner.id)
            logger.debug(f"Can update (own resource): {result}")
            return result
        logger.debug("Cannot update: no permission or not own resource")
        return False
    elif action == 'delete':
        if permission.can_manage_others:
            result = permission.can_delete
            logger.debug(f"Can delete (manage others): {result}")
            return result
        elif permission.can_delete and resource_owner:
            result = str(user.id) == str(resource_owner.id)
            logger.debug(f"Can delete (own resource): {result}")
            return result
        logger.debug("Cannot delete: no permission or not own resource")
        return False
    
    return False


def can_user_manage_roles(user):
    """Проверяет, может ли пользователь управлять ролями."""
    return user_is_admin(user)


def can_user_manage_permissions(user):
    """Проверяет, может ли пользователь управлять разрешениями."""
    return user_is_admin(user)


def can_user_manage_users(user):
    """Проверяет, может ли пользователь управлять пользователями."""
    return user_is_admin(user)
