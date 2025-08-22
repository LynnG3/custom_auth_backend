from typing import Any
import uuid
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .factories import UserFactory


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
    """Создает админа для тестирования."""
    return user_factory.create_admin()


@pytest.fixture
def authenticated_client(api_client, user):
    """API клиент с аутентифицированным пользователем."""
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """API клиент с аутентифицированным админом."""
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
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
