import pytest
from django.urls import reverse
from rest_framework import status
from faker import Faker

from permissions.models import Role, UserRole
from mock_resources.models import Resource

fake = Faker('ru_RU')


class TestPermissionsAPI:
    """Тесты для API приложения permissions."""

    @pytest.mark.django_db
    def test_admin_can_list_roles(self, role_admin_client):
        """Тест что админ может получить список ролей."""
        # Создаем тестовые роли
        Role.objects.create(name='test_role1', description='Тестовая роль 1')
        Role.objects.create(name='test_role2', description='Тестовая роль 2')

        url = reverse('permissions:role-list')
        response = role_admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2

    @pytest.mark.django_db
    def test_admin_can_create_role(self, role_admin_client):
        """Тест что админ может создать роль."""
        role_data = {
            'name': 'new_role',
            'description': 'Новая роль'
        }

        url = reverse('permissions:role-list')
        response = role_admin_client.post(url, role_data)

        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")

        # Проверяем что роль создана в базе
        try:
            role = Role.objects.get(name='new_role')
            print(f"Role created in database: {role}")
        except Role.DoesNotExist:
            print("Role not found in database")

        assert response.status_code == status.HTTP_201_CREATED
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

        url = reverse('permissions:user-role-list')
        response = role_admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
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

        url = reverse('permissions:user-role-list')
        response = role_admin_client.post(url, user_role_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['user'] == user.id
        assert response.data['role'] == role.id

        user_role = UserRole.objects.get(user=user, role=role)
        assert user_role.is_active is True

    @pytest.mark.django_db
    def test_admin_can_list_resources(self, role_admin_client):
        """Тест что админ может получить список ресурсов."""
        # Создаем тестовые ресурсы
        Resource.objects.create(
            name='Test Product 1',
            resource_type='product'
        )

        Resource.objects.create(
            name='Test Product 2',
            resource_type='product'
        )

        url = reverse('resources:resource-list')
        response = role_admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2

    @pytest.mark.django_db
    def test_admin_can_create_resource(self, role_admin_client):
        """Тест что админ может создать ресурс."""
        resource_data = {
            'name': 'New Product',
            'resource_type': 'product'
        }

        url = reverse('resources:resource-list')
        response = role_admin_client.post(url, resource_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Product'
        assert response.data['resource_type'] == 'product'

    @pytest.mark.django_db
    def test_manager_can_list_roles(self, role_manager_client):
        """Тест что менеджер может получить список ролей."""
        url = reverse('permissions:role-list')
        response = role_manager_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_manager_cannot_create_role(self, role_manager_client):
        """Тест что менеджер НЕ может создать роль."""
        role_data = {
            'name': 'new_role',
            'description': 'Новая роль'
        }

        url = reverse('permissions:role-list')
        response = role_manager_client.post(url, role_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_manager_can_list_user_roles(self, role_manager_client):
        """Тест что менеджер может получить список ролей пользователей."""
        url = reverse('permissions:user-role-list')
        response = role_manager_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_manager_cannot_assign_role(self, role_manager_client, user_factory):
        """Тест что менеджер НЕ может назначить роль."""
        user = user_factory.create_user()
        role = Role.objects.create(name='test_role', description='Тестовая роль')

        user_role_data = {
            'user': user.id,
            'role': role.id,
            'is_active': True
        }

        url = reverse('permissions:user-role-list')
        response = role_manager_client.post(url, user_role_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_regular_user_cannot_access_permissions(self, role_user_client):
        """Тест что обычный пользователь не может получить доступ к разрешениям."""
        urls_to_test = [
            reverse('permissions:role-list'),
        ]
        
        for url in urls_to_test:
            response = role_user_client.get(url)
            assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_regular_user_can_list_user_roles(self, role_user_client):
        """Тест что обычный пользователь может получить список ролей пользователей."""
        url = reverse('permissions:user-role-list')
        response = role_user_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_unauthenticated_user_cannot_access_permissions(self, api_client):
        """Тест что неаутентифицированный пользователь не может получить доступ к разрешениям."""
        urls_to_test = [
            reverse('permissions:role-list'),
            reverse('permissions:user-role-list'),
        ]

        for url in urls_to_test:
            response = api_client.get(url)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_guest_can_read_products(self, api_client):
        """Тест что гость может читать ресурсы заданного типа (product)."""
        # Создаем тестовый продукт
        Resource.objects.create(
            name='Public Product',
            resource_type='product'
        )

        url = reverse('resources:resource-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
