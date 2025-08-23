from functools import wraps
from rest_framework.exceptions import PermissionDenied
from .utils import get_user_role, can_user_access_resource


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


def require_resource_permission(resource_type, action):
    """Декоратор для проверки прав доступа к ресурсу."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Требуется аутентификация")

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
