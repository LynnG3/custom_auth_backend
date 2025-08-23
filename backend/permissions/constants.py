"""
Константы для системы разрешений.
"""

# Названия ресурсов
RESOURCE_USERS = 'users'
RESOURCE_PRODUCTS = 'products'
RESOURCE_ORDERS = 'orders'
RESOURCE_PERMISSIONS = 'permissions'

# Типы ресурсов
RESOURCE_TYPE_MODULE = 'module'
RESOURCE_TYPE_OBJECT = 'object'

# Названия прав
PERMISSION_READ = 'read_permission'
PERMISSION_READ_ALL = 'read_all_permission'
PERMISSION_CREATE = 'create_permission'
PERMISSION_UPDATE = 'update_permission'
PERMISSION_UPDATE_ALL = 'update_all_permission'
PERMISSION_DELETE = 'delete_permission'
PERMISSION_DELETE_ALL = 'delete_all_permission'

# Роли
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
ROLE_USER = 'user'
ROLE_GUEST = 'guest'

# Кэш
PERMISSION_CACHE_TIMEOUT = 300  # 5 минут
USER_ROLES_CACHE_TIMEOUT = 600  # 10 минут

# Сообщения об ошибках
ERROR_UNAUTHORIZED = 'Требуется аутентификация'
ERROR_FORBIDDEN = 'Недостаточно прав для выполнения операции'
ERROR_ADMIN_REQUIRED = 'Требуется роль администратора'
ERROR_RESOURCE_NOT_FOUND = 'Ресурс не найден'

RESOURCE_TYPES = [
        ('product', 'Продукт'),
        ('order', 'Заказ'),
        ('user', 'Пользователь'),
    ]
