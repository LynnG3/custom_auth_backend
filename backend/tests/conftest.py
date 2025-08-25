from typing import Any
import uuid
import pytest
from rest_framework.test import APIClient

from .factories import UserFactory
from permissions.models import Role, UserRole, ResourceType

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
    def create_role(
            name='test_role',
            description='Тестовая роль',
            is_default=False
        ):
        return Role.objects.create(
            name=name,
            description=description,
            is_default=is_default
        )
    return create_role


@pytest.fixture
def resource_type_factory():
    """Фабрика для создания типов ресурсов."""
    def create_resource_type(name='test_resource', **kwargs):
        return ResourceType.objects.create(
            name=name,
            **kwargs
        )
    return create_resource_type


def create_authenticated_client(api_client, user, role_name):
    """Создает аутентифицированный клиент с определенной ролью."""
    # Получаем или создаем роль
    role, _ = Role.objects.get_or_create(
        name=role_name,
        defaults={'description': f'Роль {role_name}'}
    )

    # Назначаем роль пользователю
    UserRole.objects.get_or_create(
        user=user,
        role=role,
        defaults={'assigned_by': user, 'is_active': True}
    )

    # Создаем JWT токен
    viewset = UserViewSet()
    token = viewset._create_jwt_token(user)

    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return api_client


@pytest.fixture
def role_user_client(api_client, user_factory):
    """API клиент с пользователем, имеющим роль 'user'."""
    user = user_factory.create_user()
    return create_authenticated_client(api_client, user, 'user')


@pytest.fixture
def role_manager_client(api_client, user_factory):
    """API клиент с пользователем, имеющим роль 'manager'."""
    user = user_factory.create_user()

    return create_authenticated_client(api_client, user, 'manager')


@pytest.fixture
def role_admin_client(api_client, user_factory):
    """API клиент с пользователем, имеющим роль 'admin'."""
    user = user_factory.create_user()
    return create_authenticated_client(api_client, user, 'admin')
