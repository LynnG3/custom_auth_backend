import pytest
from django.urls import reverse
from rest_framework import status

from permissions.models import Role, ResourceType, RolePermission
from mock_resources.models import Resource


class BaseTestCase:
    """Базовый класс для тестов с общими методами."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Автоматическая настройка тестовых данных."""
        self.setup_roles()
        self.setup_resource_types()

    def setup_roles(self):
        """Создание ролей."""
        self.admin_role, _ = Role.objects.get_or_create(
            name='admin',
            defaults={'description': 'Администратор системы'}
        )
        self.manager_role, _ = Role.objects.get_or_create(
            name='manager',
            defaults={'description': 'Менеджер'}
        )
        self.user_role, _ = Role.objects.get_or_create(
            name='user',
            defaults={'description': 'Обычный пользователь'}
        )

    def setup_resource_types(self):
        """Создает базовые типы ресурсов."""
        self.product_type, _ = ResourceType.objects.get_or_create(
            name='product',
            defaults={'description': 'Товары и услуги'}
        )
        self.order_type, _ = ResourceType.objects.get_or_create(
            name='order',
            defaults={'description': 'Заказы пользователей'}
        )
        self.user_resource_type, _ = ResourceType.objects.get_or_create(
            name='user',
            defaults={'description': 'Пользователи системы'}
        )

    def create_resource(self, name, resource_type=None, owner=None):
        """Создает тестовый ресурс."""
        if resource_type is None:
            resource_type = self.product_type
        return Resource.objects.create(
            name=name,
            resource_type=resource_type,
            owner=owner
        )

    def setup_permissions(self, role, **permissions):
        """Настраивает разрешения для роли."""
        for resource_type in [
            self.product_type, self.order_type, self.user_resource_type
        ]:
            permission, _ = RolePermission.objects.get_or_create(
                role=role,
                resource_type=resource_type,
                defaults={
                    'can_read': True,
                    'can_create': False,
                    'can_update': False,
                    'can_delete': False,
                    'can_manage_others': False
                }
            )

            # Обновляем разрешения
            for key, value in permissions.items():
                if hasattr(permission, key):
                    setattr(permission, key, value)
            permission.save()

    def assert_response_success(
            self, response, expected_status=status.HTTP_200_OK
        ):
        """Проверяет успешный ответ."""
        assert response.status_code == expected_status

    def assert_response_error(self, response, expected_status):
        """Проверяет ответ с ошибкой."""
        assert response.status_code == expected_status


class BaseAPITestCase(BaseTestCase):
    """Базовый класс для API тестов."""

    @pytest.fixture(autouse=True)
    def setup_client(self, api_client):
        """Настраивает API клиент."""
        self.client = api_client

    def get_url(self, url_name, **kwargs):
        """Получает URL по имени."""
        return reverse(url_name, kwargs=kwargs)

    def make_request(self, method, url_name, data=None, **kwargs):
        """Выполняет HTTP запрос."""
        url = self.get_url(url_name, **kwargs)
        method_func = getattr(self.client, method.lower())

        if data is not None:
            response = method_func(url, data, format='json')
        else:
            response = method_func(url)

        return response
