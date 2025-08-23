import pytest
from faker import Faker

from mock_resources.models import Resource
from permissions.models import Role, UserRole, RolePermission

fake = Faker('ru_RU')


class TestPermissionsIntegration:
    """Интеграционные тесты для работы permissions с users."""

    @pytest.mark.django_db
    def test_user_gets_default_role_on_creation(self, user_factory):
        """Тест что пользователь автоматически получает роль 'user' при создании."""
        user = user_factory.create_user()

        # Проверяем что у пользователя есть роль
        user_roles = UserRole.objects.filter(user=user, is_active=True)
        assert user_roles.exists()

        user_role = user_roles.first().role
        assert user_role.name == 'user'
    
    @pytest.mark.django_db
    def test_user_with_multiple_roles(self, user_factory):
        """Тест что пользователь может иметь несколько ролей."""
        user = user_factory.create_user()
        
        # Создаем дополнительные роли с уникальными именами
        manager_role = Role.objects.create(name='test_manager', description='Тестовый менеджер')
        test_user_role = Role.objects.create(name='test_user_role', description='Тестовая роль пользователя')
        
        # Назначаем роли пользователю
        UserRole.objects.create(user=user, role=manager_role, assigned_by=user)
        UserRole.objects.create(user=user, role=test_user_role, assigned_by=user)
        
        # Проверяем что у пользователя несколько ролей
        user_roles = UserRole.objects.filter(user=user, is_active=True)
        assert user_roles.count() >= 3  # user + manager + test_user_role
        
        # Проверяем что можно получить роль (первую активную)
        from permissions.utils import get_user_role
        user_role = get_user_role(user)
        assert user_role in ['user', 'test_manager', 'test_user_role']
    
    @pytest.mark.django_db
    def test_role_permissions_work_with_resources(self, user_factory):
        """Тест что разрешения ролей работают с ресурсами."""
        # Создаем роль с разрешениями
        role = Role.objects.create(name='test_role', description='Тестовая роль')
        
        # Проверяем что разрешения созданы сигналом
        permissions = RolePermission.objects.filter(role=role)
        print(f"Created permissions: {list(permissions.values())}")
        
        # Обновляем разрешения (они уже созданы сигналом)
        permission = RolePermission.objects.get(role=role, resource_type='product')
        permission.can_create = True
        permission.can_read = True
        permission.can_update = True
        permission.can_delete = False
        permission.save()
        
        # Создаем пользователя с этой ролью
        user = user_factory.create_user()
        
        # Удаляем автоматически назначенную роль 'user'
        UserRole.objects.filter(user=user).delete()
        
        # Назначаем нашу тестовую роль
        user_role = UserRole.objects.create(user=user, role=role, assigned_by=user)
        print(f"User role created: {user_role}")
        
        # Проверяем что разрешения работают
        from permissions.utils import can_user_access_resource, get_user_role
        
        # Отладочная информация
        print(f"User: {user.email}")
        print(f"User role: {get_user_role(user)}")
        print(f"Permission check result: {can_user_access_resource(user, 'product', 'create')}")
        
        assert can_user_access_resource(user, 'product', 'create') is True
        assert can_user_access_resource(user, 'product', 'read') is True
        
        # Для update нужен resource_owner или can_manage_others=True
        # Создаем ресурс, принадлежащий пользователю
        resource = Resource.objects.create(
            name='Test Product',
            resource_type='product',
            owner=user
        )
        
        assert can_user_access_resource(user, 'product', 'update', resource.owner) is True
    
    @pytest.mark.django_db
    def test_resource_owner_permissions(self, user_factory):
        """Тест что пользователь может управлять только своими ресурсами."""
        # Создаем пользователя
        user = user_factory.create_user()
        
        # Создаем ресурс, принадлежащий пользователю
        resource = Resource.objects.create(
            name='My Product',
            resource_type='product',
            owner=user
        )
        
        # Создаем роль с правами на управление своими ресурсами
        role = Role.objects.create(name='test_role', description='Тестовая роль')
        
        # Обновляем разрешения
        permission = RolePermission.objects.get(role=role, resource_type='product')
        permission.can_update = True
        permission.can_delete = True
        permission.can_manage_others = False
        permission.save()
        
        UserRole.objects.create(user=user, role=role, assigned_by=user)
        
        # Проверяем права
        from permissions.utils import can_user_access_resource
        
        # Может управлять своим ресурсом
        assert can_user_access_resource(user, 'product', 'update', resource.owner) is True
        assert can_user_access_resource(user, 'product', 'delete', resource.owner) is True
        
        # Не может управлять чужими ресурсами
        other_user = user_factory.create_user()
        assert can_user_access_resource(user, 'product', 'update', other_user) is False
        assert can_user_access_resource(user, 'product', 'delete', other_user) is False