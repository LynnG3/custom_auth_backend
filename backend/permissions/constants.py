"""
Константы для системы разрешений.
"""

# Кэш
PERMISSION_CACHE_TIMEOUT = 300  # 5 минут
USER_ROLES_CACHE_TIMEOUT = 600  # 10 минут

# Типы ресурсов
RESOURCE_TYPES = [
        ('product', 'Продукт'),
        ('order', 'Заказ'),
        ('user', 'Пользователь'),
    ]
