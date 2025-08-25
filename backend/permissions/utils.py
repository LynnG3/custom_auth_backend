from django.core.cache import cache
import logging

from .models import UserRole, RolePermission, ResourceType

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
    
    # 🔍 ЛОГИРУЕМ поиск разрешений
    logger.debug(f"=== get_role_permissions DEBUG ===")
    logger.debug(f"Role name: {role_name}")
    logger.debug(f"Resource type: {resource_type} (type: {type(resource_type)})")
    
    try:
        # Поддерживаем как строковые названия, так и объекты ResourceType
        if isinstance(resource_type, str):
            logger.debug(f"Searching by string resource type: {resource_type}")
            permission = RolePermission.objects.get(
                role__name=role_name, 
                resource_type__name=resource_type,
                resource_type__is_active=True
            )
        else:
            logger.debug(f"Searching by ResourceType object: {resource_type}")
            permission = RolePermission.objects.get(
                role__name=role_name, 
                resource_type=resource_type,
                resource_type__is_active=True
            )
        
        logger.debug(f"Found permission: {permission}")
        return permission
        
    except RolePermission.DoesNotExist:
        logger.warning(f"RolePermission not found for role '{role_name}' on resource '{resource_type}'")
        
        # 🔍 ЛОГИРУЕМ что есть в базе
        try:
            role = UserRole.objects.get(role__name=role_name) # Assuming UserRole has a role field
            logger.debug(f"Role exists: {role}")
        except UserRole.DoesNotExist:
            logger.error(f"Role '{role_name}' not found")
            return None
            
        try:
            if isinstance(resource_type, str):
                resource = ResourceType.objects.get(name=resource_type)
            else:
                resource = resource_type
            logger.debug(f"Resource type exists: {resource}")
        except ResourceType.DoesNotExist:
            logger.error(f"ResourceType '{resource_type}' not found")
            return None
            
        # 🔍 ЛОГИРУЕМ существующие разрешения
        existing_permissions = RolePermission.objects.filter(
            role=role, 
            resource_type=resource
        )
        logger.debug(f"Existing permissions for this role/resource: {list(existing_permissions)}")
        
        return None


def can_user_access_resource(user, resource_type, action, resource_owner=None):
    """
    Проверяет, может ли пользователь выполнить действие с ресурсом.

    Args:
        user: Пользователь
        resource_type: Тип ресурса (строка или объект ResourceType)
        action: Действие ('create', 'read', 'update', 'delete')
        resource_owner: Владелец ресурса (для проверки своих/чужих)
    """
    logger = logging.getLogger(__name__)
    
    # 🔍 ЛОГИРУЕМ входные параметры
    logger.debug(f"=== can_user_access_resource DEBUG ===")
    logger.debug(f"User: {user.email}")
    logger.debug(f"Resource type: {resource_type}")
    logger.debug(f"Action: {action}")
    logger.debug(f"Resource owner: {resource_owner}")

    if not user.is_authenticated:
        logger.debug("User not authenticated")
        # Гости могут только читать активные ресурсы
        if action == 'read':
            try:
                if isinstance(resource_type, str):
                    resource = ResourceType.objects.get(
                        name=resource_type, is_active=True
                    )
                else:
                    resource = resource_type
                return resource.is_active
            except ResourceType.DoesNotExist:
                return False
        return False

    user_role = get_user_role(user)
    logger.debug(f"User role: {user_role}")

    if not user_role:
        logger.warning(f"User {user.email} has no role assigned")
        return False

    # 🔍 ЛОГИРУЕМ поиск разрешений
    logger.debug(f"Looking for permissions for role '{user_role}' on resource '{resource_type}'")
    
    permission = get_role_permissions(user_role, resource_type)
    logger.debug(f"Found permission: {permission}")
    
    if not permission:
        logger.warning(f"No permission found for role {user_role} on {resource_type}")
        return False

    # 🔍 ЛОГИРУЕМ детали разрешения
    logger.debug(f"Permission details:")
    logger.debug(f"  - Role: {permission.role.name}")
    logger.debug(f"  - Resource type: {permission.resource_type.name}")
    logger.debug(f"  - Can read: {permission.can_read}")
    logger.debug(f"  - Can create: {permission.can_create}")
    logger.debug(f"  - Can update: {permission.can_update}")
    logger.debug(f"  - Can delete: {permission.can_delete}")
    logger.debug(f"  - Can manage others: {permission.can_manage_others}")

    # Проверяем действие
    if action == 'create':
        result = permission.can_create
        logger.debug(f"Action 'create' result: {result}")
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


def can_user_manage_resource_types(user):
    """Проверяет, может ли пользователь управлять типами ресурсов."""
    return user_is_admin(user)


def get_active_resource_types():
    """Получает все активные типы ресурсов."""
    return ResourceType.objects.filter(is_active=True)


def get_resource_type_by_name(name):
    """Получает тип ресурса по названию."""
    try:
        return ResourceType.objects.get(name=name, is_active=True)
    except ResourceType.DoesNotExist:
        return None
