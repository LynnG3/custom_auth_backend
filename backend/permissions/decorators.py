from functools import wraps
from rest_framework.exceptions import PermissionDenied
import logging

from permissions.models import ResourceType
from .utils import get_user_role, can_user_access_resource


logger = logging.getLogger(__name__)


def require_admin():
    """Декоратор для проверки прав администратора."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Требуется аутентификация")
            user_role = get_user_role(request.user)
            if user_role != 'admin':
                raise PermissionDenied("Требуются права администратора")

            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator


def require_admin_or_manager():
    """Декоратор для проверки прав администратора или менеджера."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Требуется аутентификация")
            
            user_role = get_user_role(request.user)
            if user_role not in ['admin', 'manager']:
                raise PermissionDenied(
                    "Требуется роль администратора или менеджера"
                )
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator


def require_user_or_higher():
    """Декоратор для проверки прав пользователя или выше."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Требуется аутентификация")

            user_role = get_user_role(request.user)
            if user_role not in ['admin', 'manager', 'user']:
                raise PermissionDenied("Требуется роль пользователя или выше")

            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator


def require_dynamic_permission(action):
    """
    Динамический декоратор для проверки прав доступа к ресурсу.
    
    Args:
        action: Действие ('create', 'read', 'update', 'delete')
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Требуется аутентификация")

            logger.debug(f"=== require_dynamic_permission DEBUG ===")
            logger.debug(f"Action: {action}")
            logger.debug(f"ViewSet: {self.__class__.__name__}")

            # Получаем тип ресурса из ViewSet
            resource_type = getattr(self, 'resource_type', None)
            logger.debug(f"Resource type from ViewSet: {resource_type}")
            
            if not resource_type:
                # Пытаемся определить из модели
                if hasattr(self, 'queryset') and self.queryset.model:
                    # Получаем название модели и ищем соответствующий ResourceType
                    model_name = self.queryset.model._meta.model_name
                    logger.debug(f"Model name: {model_name}")
                    
                    if model_name == 'resource':
                        # Для Resource модели определяем тип из request.data
                        if action == 'create' and request.data.get('resource_type'):
                            try:
                                resource_type_obj = ResourceType.objects.get(
                                    id=request.data['resource_type']
                                )
                                resource_type = resource_type_obj.name
                                logger.debug(f"Resource type from request.data: {resource_type}")
                            except ResourceType.DoesNotExist:
                                logger.error(f"ResourceType with id {request.data['resource_type']} not found")
                                raise PermissionDenied("Неверный тип ресурса")
                        else:
                            # Для других действий пытаемся получить из объекта
                            resource_type = 'product'  # По умолчанию
                            logger.debug(f"Using default resource type: {resource_type}")
                    else:
                        resource_type = model_name
                        logger.debug(f"Using model name as resource type: {resource_type}")

            logger.debug(f"Final resource type: {resource_type}")

            # Получаем владельца ресурса для проверки доступа
            resource_owner = None
            if action in ['update', 'delete'] and hasattr(self, 'get_object'):
                try:
                    obj = self.get_object()
                    if hasattr(obj, 'owner'):
                        resource_owner = obj.owner
                except:
                    pass

            if not can_user_access_resource(
                request.user, resource_type, action, resource_owner
            ):
                raise PermissionDenied(
                    f"Недостаточно прав для {action} ресурса {resource_type}"
                )

            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator
