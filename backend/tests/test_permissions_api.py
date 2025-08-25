import logging
import pytest
from rest_framework import status
from faker import Faker

from permissions.models import Role, UserRole, ResourceType
from .base import BaseAPITestCase

fake = Faker('ru_RU')


logger = logging.getLogger(__name__)


class TestPermissionsAPI(BaseAPITestCase):
    """Тесты для API приложения permissions."""

    @pytest.mark.django_db
    def test_admin_can_list_roles(self, role_admin_client):
        """Тест что админ может получить список ролей."""
        # Создаем тестовые роли
        Role.objects.create(name='test_role1', description='Тестовая роль 1')
        Role.objects.create(name='test_role2', description='Тестовая роль 2')

        response = role_admin_client.get(self.get_url('permissions:role-list'))

        self.assert_response_success(response)
        assert len(response.data) >= 2

    @pytest.mark.django_db
    def test_admin_can_create_role(self, role_admin_client):
        """Тест что админ может создать роль."""
        role_data = {
            'name': 'new_role',
            'description': 'Новая роль'
        }

        response = role_admin_client.post(
            self.get_url('permissions:role-list'),
            role_data
        )

        self.assert_response_success(response, status.HTTP_201_CREATED)
        assert response.data['name'] == 'new_role'

        # Проверяем что роль создана в базе
        role = Role.objects.get(name='new_role')
        assert role.description == 'Новая роль'

    @pytest.mark.django_db
    def test_admin_can_list_user_roles(self, role_admin_client, user_factory):
        """Тест что админ может получить список ролей пользователей."""
        # Создаем тестовых пользователей с ролями
        user1 = user_factory.create_user()
        user2 = user_factory.create_user()
        role = Role.objects.create(
            name='test_role',
            description='Тестовая роль'
        )

        UserRole.objects.create(user=user1, role=role, assigned_by=user1)
        UserRole.objects.create(user=user2, role=role, assigned_by=user1)

        response = role_admin_client.get(
            self.get_url('permissions:user-role-list')
        )
        self.assert_response_success(response)

        assert len(response.data) >= 2

    @pytest.mark.django_db
    def test_admin_can_assign_role_to_user(
        self,
        role_admin_client,
        user_factory
    ):
        """Тест что админ может назначить роль пользователю."""
        user = user_factory.create_user()
        role = Role.objects.create(
            name='test_role',
            description='Тестовая роль'
        )

        user_role_data = {
            'user': user.id,
            'role': role.id,
            'is_active': True
        }

        response = role_admin_client.post(
            self.get_url('permissions:user-role-list'),
            user_role_data
        )
        self.assert_response_success(response, status.HTTP_201_CREATED)

        assert response.data['user'] == user.id
        assert response.data['role'] == role.id

        user_role = UserRole.objects.get(user=user, role=role)
        assert user_role.is_active is True

    @pytest.mark.django_db
    def test_admin_can_list_resources(self, role_admin_client):
        """Тест что админ может получить список ресурсов."""
        # Создаем тестовые ресурсы
        self.create_resource('Test Product 1')
        self.create_resource('Test Product 2')

        response = role_admin_client.get(
            self.get_url('resources:resource-list')
        )
        self.assert_response_success(response)
        assert len(response.data) >= 2

    @pytest.mark.django_db
    def test_admin_can_create_resource(self, role_admin_client):
        """Тест что админ может создать ресурс."""

        # Настраиваем разрешения для админа
        self.setup_permissions(
            self.admin_role,
            can_create=True,
            can_read=True,
            can_update=True,
            can_delete=True,
            can_manage_others=True
        )

        resource_data = {
            'name': 'New Product',
            'resource_type': self.product_type.id
        }

        response = role_admin_client.post(
            self.get_url('resources:resource-list'),
            resource_data
        )

        self.assert_response_success(response, status.HTTP_201_CREATED)
        assert response.data['name'] == 'New Product'
        assert response.data['resource_type'] == self.product_type.id


    @pytest.mark.django_db
    def test_admin_can_manage_resource_types(self, role_admin_client):
        """Тест что админ может управлять типами ресурсов."""
        # Создание типа ресурса
        resource_type_data = {
            'name': 'invoice',
            'description': 'Счета пользователей'
        }

        response = role_admin_client.post(
            self.get_url('permissions:resource-types-list'),
            resource_type_data
        )

        self.assert_response_success(response, status.HTTP_201_CREATED)
        assert response.data['name'] == 'invoice'

        # Проверяем что ресурс создан в базе
        resource_type = ResourceType.objects.get(name='invoice')
        assert resource_type.description == 'Счета пользователей'

    @pytest.mark.django_db
    def test_manager_can_list_roles(self, role_manager_client):
        """Тест что менеджер может получить список ролей."""
        response = role_manager_client.get(
            self.get_url('permissions:role-list')
        )
        self.assert_response_success(response)

    @pytest.mark.django_db
    def test_manager_cannot_create_role(self, role_manager_client):
        """Тест что менеджер не может создать роль."""
        role_data = {
            'name': 'new_role',
            'description': 'Новая роль'
        }

        response = role_manager_client.post(
            self.get_url('permissions:role-list'),
            role_data
        )
        self.assert_response_error(response, status.HTTP_403_FORBIDDEN)

    @pytest.mark.django_db
    def test_manager_can_list_user_roles(self, role_manager_client):
        """Тест что менеджер может получить список ролей пользователей."""
        response = role_manager_client.get(
            self.get_url('permissions:user-role-list')
        )
        self.assert_response_success(response)

    @pytest.mark.django_db
    def test_manager_cannot_assign_role(
        self, role_manager_client, user_factory
    ):
        """Тест что менеджер не может назначить роль."""
        user = user_factory.create_user()
        role = Role.objects.create(
            name='test_role', description='Тестовая роль'
        )

        user_role_data = {
            'user': user.id,
            'role': role.id,
            'is_active': True
        }

        response = role_manager_client.post(
            self.get_url('permissions:user-role-list'),
            user_role_data
        )

        self.assert_response_error(response, status.HTTP_403_FORBIDDEN)

    @pytest.mark.django_db
    def test_regular_user_can_list_user_roles(self, role_user_client):
        """Тест что обычный пользователь
        может получить список ролей пользователей."""
        response = role_user_client.get(
            self.get_url('permissions:user-role-list')
        )
        self.assert_response_success(response)

    @pytest.mark.django_db
    def test_unauthenticated_user_cannot_access_permissions(self, api_client):
        """Тест что неаутентифицированный пользователь
        не может получить доступ к разрешениям."""
        urls_to_test = [
            'permissions:role-list',
            'permissions:user-role-list',
        ]

        for url_name in urls_to_test:
            response = api_client.get(self.get_url(url_name))
            self.assert_response_error(response, status.HTTP_401_UNAUTHORIZED)

    @pytest.mark.django_db
    def test_guest_can_read_products(self, api_client):
        """Тест что гость может читать ресурсы заданного типа (product)."""
        # Создаем тестовый продукт
        self.create_resource('Public Product')

        response = api_client.get(
            self.get_url('resources:resource-list')
        )
        self.assert_response_success(response)
        assert len(response.data) >= 1

    @pytest.mark.django_db
    def test_resource_type_api_endpoints(self, role_admin_client):
        """Тест API эндпоинтов для типов ресурсов."""
        # Создаем тип ресурса
        resource_type = ResourceType.objects.create(
            name='test_resource',
            description='Описание тестового ресурса'
        )

        # Тест получения списка
        response = role_admin_client.get(
            self.get_url('permissions:resource-types-list')
        )
        self.assert_response_success(response)
        assert len(response.data) >= 1

        # Тест получения деталей
        detail_url = self.get_url(
            'permissions:resource-types-detail',
            pk=resource_type.id
        )
        response = role_admin_client.get(detail_url)
        self.assert_response_success(response)
        assert response.data['name'] == 'test_resource'

        # Тест обновления
        update_data = {'description': 'Обновленное описание'}
        response = role_admin_client.patch(detail_url, update_data)
        self.assert_response_success(response)
        assert response.data['description'] == 'Обновленное описание'

        # Тест деактивации
        response = role_admin_client.delete(detail_url)
        self.assert_response_success(response, status.HTTP_204_NO_CONTENT)

        # Проверяем что ресурс деактивирован
        resource_type.refresh_from_db()
        assert resource_type.is_active is False
