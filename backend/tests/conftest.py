from typing import Any
import uuid
import pytest
from rest_framework.test import APIClient

from .factories import UserFactory
from permissions.models import Role
from users.views import UserViewSet


@pytest.fixture
def api_client() -> APIClient:
    """API клиент для тестирования."""
    return APIClient()


@pytest.fixture
def user_factory() -> UserFactory:
    """Фабрика для создания пользователей."""
    return UserFactory()


@pytest.fixture
def user(user_factory):
    """Создает тестового пользователя."""
    return user_factory.create_user()


@pytest.fixture
def admin_user(user_factory):
    """Создает админа для тестирования (Django superuser)."""
    return user_factory.create_admin()


@pytest.fixture
def authenticated_client(api_client, user):
    """API клиент с аутентифицированным пользователем."""
    # Создаем JWT токен через кастомную логику
    viewset = UserViewSet()
    token = viewset._create_jwt_token(user)
    
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """API клиент с Django superuser (для тестов users)."""
    # Создаем JWT токен через кастомную логику
    viewset = UserViewSet()
    token = viewset._create_jwt_token(admin_user)
    
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return api_client


@pytest.fixture
def user_data_factory() -> dict[str, Any]:
    """Фабрика для данных пользователя."""
    factory = UserFactory()
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    return {
        "email": email,
        "first_name": factory.first_name,
        "last_name": factory.last_name,
        "password": factory.password,
        "password_confirm": factory.password_confirm,
    }


@pytest.fixture
def admin_data_factory() -> dict[str, Any]:
    """Фабрика для данных админа."""
    factory = UserFactory()
    email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    return {
        "email": email,
        "first_name": factory.first_name,
        "last_name": factory.last_name,
        "password": factory.password,
        "password_confirm": factory.password_confirm,
    }


@pytest.fixture
def role_factory():
    """Фабрика для создания ролей."""
    def create_role(name='test_role', description='Тестовая роль', is_default=False):
        return Role.objects.create(
            name=name,
            description=description,
            is_default=is_default
        )
    return create_role


@pytest.fixture
def resource_permission_factory():
    """Фабрика для создания разрешений на ресурсы."""
    def create_permission(role, resource_name='users', resource_type='module', **permissions):
        return ResourcePermission.objects.create(
            role=role,
            resource_name=resource_name,
            resource_type=resource_type,
            **permissions
        )
    return create_permission


@pytest.fixture
def role_user_client(api_client, user_factory):
    """API клиент с пользователем, имеющим роль 'user' (для тестов permissions)."""
    user = user_factory.create_user()
    
    # Пользователь уже имеет роль 'user' от сигнала
    # Просто обновляем разрешения для этой роли
    from permissions.models import Role, UserRole, RolePermission
    
    # Получаем существующую роль пользователя
    user_role_obj = UserRole.objects.get(user=user, is_active=True).role
    
    # Обновляем разрешения для роли пользователя
    for resource_type in ['product', 'order', 'user']:
        permission, created = RolePermission.objects.get_or_create(
            role=user_role_obj,
            resource_type=resource_type,
            defaults={
                'can_create': True,
                'can_read': True,
                'can_update': True,
                'can_delete': False,
                'can_manage_others': False
            }
        )
        if not created:
            permission.can_create = True
            permission.can_read = True
            permission.can_update = True
            permission.can_delete = False
            permission.can_manage_others = False
            permission.save()
    
    # Создаем JWT токен
    viewset = UserViewSet()
    token = viewset._create_jwt_token(user)
    
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return api_client


@pytest.fixture
def role_manager_client(api_client, user_factory):
    """API клиент с пользователем, имеющим роль 'manager' (для тестов permissions)."""
    user = user_factory.create_user()
    
    # Получаем существующую роль 'manager' или создаем её
    from permissions.models import Role, UserRole, RolePermission
    manager_role, created = Role.objects.get_or_create(
        name='manager',
        defaults={
            'description': 'Менеджер',
            'is_default': False
        }
    )
    
    # Используем get_or_create для UserRole - безопасно!
    user_role, created = UserRole.objects.get_or_create(
        user=user,
        role=manager_role,
        defaults={
            'assigned_by': user,
            'is_active': True
        }
    )
    
    # Если роль уже была 'user', деактивируем её
    if not created and user_role.role.name == 'user':
        user_role.is_active = False
        user_role.save()
        # Создаем новую активную роль manager
        user_role = UserRole.objects.create(
            user=user,
            role=manager_role,
            assigned_by=user,
            is_active=True
        )
    
    # Обновляем разрешения для менеджера
    for resource_type in ['product', 'order', 'user']:
        permission, created = RolePermission.objects.get_or_create(
            role=manager_role,
            resource_type=resource_type,
            defaults={
                'can_create': True,
                'can_read': True,
                'can_update': True,
                'can_delete': False,
                'can_manage_others': False
            }
        )
        if not created:
            permission.can_create = True
            permission.can_read = True
            permission.can_update = True
            permission.can_delete = False
            permission.can_manage_others = False
            permission.save()
    
    viewset = UserViewSet()
    token = viewset._create_jwt_token(user)
    
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return api_client


@pytest.fixture
def role_admin_client(api_client, user_factory):
    """API клиент с пользователем, имеющим роль 'admin' (для тестов permissions)."""
    user = user_factory.create_user()
    
    # Получаем существующую роль 'admin' или создаем её
    from permissions.models import Role, UserRole, RolePermission
    admin_role, created = Role.objects.get_or_create(
        name='admin',
        defaults={
            'description': 'Администратор системы',
            'is_default': False
        }
    )
    
    # Используем get_or_create для UserRole - безопасно!
    user_role, created = UserRole.objects.get_or_create(
        user=user,
        role=admin_role,
        defaults={
            'assigned_by': user,
            'is_active': True
        }
    )
    
    # Если роль уже была 'user', деактивируем её
    if not created and user_role.role.name == 'user':
        user_role.is_active = False
        user_role.save()
        # Создаем новую активную роль admin
        user_role = UserRole.objects.create(
            user=user,
            role=admin_role,
            assigned_by=user,
            is_active=True
        )
    
    # Обновляем разрешения для админа
    for resource_type in ['product', 'order', 'user']:
        permission, created = RolePermission.objects.get_or_create(
            role=admin_role,
            resource_type=resource_type,
            defaults={
                'can_create': True,
                'can_read': True,
                'can_update': True,
                'can_delete': True,
                'can_manage_others': True
            }
        )
        if not created:
            permission.can_create = True
            permission.can_read = True
            permission.can_update = True
            permission.can_delete = True
            permission.can_manage_others = True
            permission.save()
    
    # Создаем JWT токен
    viewset = UserViewSet()
    token = viewset._create_jwt_token(user)
    
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return api_client
