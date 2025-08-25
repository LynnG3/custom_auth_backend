from django.core.cache import cache
import pytest
from faker import Faker

from mock_resources.models import Resource
from permissions.models import Role, UserRole, RolePermission, ResourceType
from permissions.utils import can_user_access_resource, get_user_role
from .base import BaseTestCase

fake = Faker('ru_RU')


class TestPermissionsIntegration(BaseTestCase):
    """Интеграционные тесты для работы permissions с users."""

    @pytest.mark.django_db
    def test_user_gets_default_role_on_creation(self, user_factory):
        """Тест что пользователь автоматически
        получает роль 'user' при создании."""
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
        manager_role = Role.objects.create(
            name='test_manager',
            description='Тестовый менеджер'
        )
        test_user_role = Role.objects.create(
            name='test_user_role',
            description='Тестовая роль пользователя'
        )

        # Назначаем роли пользователю
        UserRole.objects.create(
            user=user,
            role=manager_role,
            assigned_by=user
        )
        UserRole.objects.create(
            user=user,
            role=test_user_role,
            assigned_by=user
        )

        # Проверяем что у пользователя несколько ролей
        user_roles = UserRole.objects.filter(user=user, is_active=True)
        assert user_roles.count() >= 3  # user + manager + test_user_role

        # Проверяем что можно получить роль (первую активную)
        user_role = get_user_role(user)
        assert user_role in ['user', 'test_manager', 'test_user_role']

    @pytest.mark.django_db
    def test_role_permissions_work_with_resources(self, user_factory):
        """Тест что разрешения ролей работают с ресурсами."""

        # Создаем роль с разрешениями
        role = Role.objects.create(
            name='test_role', description='Тестовая роль'
        )

        # Обновляем разрешения используя базовый метод
        self.setup_permissions(
            role,
            can_create=True,
            can_read=True,
            can_update=True,
            can_delete=False,
            can_manage_others=False
        )
        user = user_factory.create_user()

        # Удаляем автоматически назначенную роль 'user'
        UserRole.objects.filter(user=user).delete()

        # Назначаем тестовую роль
        UserRole.objects.create(
            user=user, role=role, assigned_by=user
        )
        assert can_user_access_resource(
            user, self.product_type, 'create'
        ) is True
        assert can_user_access_resource(
            user, self.product_type, 'read'
        ) is True

        resource = self.create_resource('Test Product', owner=user)
        assert can_user_access_resource(
            user, self.product_type, 'update', resource.owner
        ) is True

    @pytest.mark.django_db
    def test_resource_owner_permissions(self, user_factory):
        """Тест что пользователь может управлять только своими ресурсами."""

        user = user_factory.create_user()
        resource = self.create_resource('My Order', owner=user)

        # Создаем роль с правами на управление своими ресурсами
        role = Role.objects.create(
            name='test_role',
            description='Тестовая роль'
        )

        # Обновляем разрешения используя базовый метод
        self.setup_permissions(
            role,
            can_update=True,
            can_delete=True,
            can_manage_others=False
        )

        UserRole.objects.create(user=user, role=role, assigned_by=user)

        # Может управлять своим ресурсом
        assert can_user_access_resource(
            user, self.order_type, 'update', resource.owner
        ) is True
        assert can_user_access_resource(
            user, self.order_type, 'delete', resource.owner
        ) is True

        # Не может управлять чужими ресурсами
        other_user = user_factory.create_user()
        assert can_user_access_resource(
            user, self.order_type, 'update', other_user
        ) is False
        assert can_user_access_resource(
            user, self.order_type, 'delete', other_user
        ) is False

    @pytest.mark.django_db
    def test_automatic_permission_creation_for_new_roles(self):
        """Тест автоматического создания разрешений для новых ролей."""
        # Создаем новую роль
        role = Role.objects.create(name='new_role', description='Новая роль')
        # Проверяем что разрешения созданы автоматически
        permissions = RolePermission.objects.filter(role=role)
        assert permissions.count() == 3  # Для product, order, user
        # Проверяем что все разрешения имеют базовые права
        for permission in permissions:
            assert permission.can_read is True  # Все роли могут читать
            assert permission.can_create is False  # Но не могут создавать по умолчанию

    @pytest.mark.django_db
    def test_automatic_permission_creation_for_new_resources(self):
        """Тест автоматического создания разрешений
        для новых типов ресурсов."""

        # Создаем новый тип ресурса
        new_resource_type = ResourceType.objects.create(
            name='invoice',
            description='Счета пользователей'
        )

        # Проверяем что разрешения созданы автоматически для всех ролей
        admin_permission = RolePermission.objects.get(
            role=self.admin_role, resource_type=new_resource_type
        )
        user_permission = RolePermission.objects.get(
            role=self.user_role, resource_type=new_resource_type
        )

        assert admin_permission is not None
        assert user_permission is not None

        # Проверяем базовые права
        assert admin_permission.can_read is True
        assert user_permission.can_read is True # так не должно быть

    @pytest.mark.django_db
    def test_role_priority_hierarchy(self, user_factory):
        """Тест иерархии приоритетов ролей (admin > manager > user)."""
        user = user_factory.create_user()

        # Назначаем пользователю роль 'user' (по умолчанию)
        user_role = UserRole.objects.get(user=user, is_active=True)
        assert user_role.role.name == 'user'
        
        # Назначаем роль 'manager' (более высокая)
        manager_role = Role.objects.get(name='manager')
        UserRole.objects.create(
            user=user,
            role=manager_role,
            assigned_by=user,
            is_active=True
        )
        
        # Проверяем что активна роль 'manager'
        active_role = get_user_role(user)
        assert active_role == 'manager'
        
        # Очищаем кэш роли пользователя
        cache.delete(f'user_role_{user.id}')
        
        # Назначаем роль 'admin' (самая высокая)
        admin_role = Role.objects.get(name='admin')
        UserRole.objects.create(
            user=user,
            role=admin_role,
            assigned_by=user,
            is_active=True
        )

        # # Проверяем что активна роль 'admin'
        active_role = get_user_role(user)
        assert active_role == 'admin'
        # Дополнительная проверка: у пользователя должно быть 3 активные роли
        active_roles = UserRole.objects.filter(user=user, is_active=True)
        assert active_roles.count() == 3

        # Проверяем что все роли активны
        role_names = [ur.role.name for ur in active_roles]
        assert 'user' in role_names
        assert 'manager' in role_names
        assert 'admin' in role_names

        # Проверяем сортировку
        sorted_role_names = sorted(role_names)
        assert sorted_role_names == ['admin', 'manager', 'user']

    @pytest.mark.django_db
    def test_resource_type_soft_delete_integration(self, user_factory):
        """Тест интеграции мягкого удаления типов ресурсов с разрешениями."""
        # Создаем новый тип ресурса
        resource_type = ResourceType.objects.create(
            name='test_resource',
            description='Тестовый ресурс для удаления'
        )
        # Создаем ресурс этого типа
        resource = self.create_resource(
            'Test Resource', resource_type=resource_type
        )
        # Проверяем что ресурс активен
        assert resource.resource_type.is_active is True
        # Мягко удаляем тип ресурса
        resource_type.is_active = False
        resource_type.save()
        # Обновляем из базы
        resource_type.refresh_from_db()
        assert resource_type.is_active is False
        # Проверяем что ресурс все еще существует, но тип неактивен
        resource.refresh_from_db()
        assert resource.resource_type.is_active is False
        # Проверяем что разрешения для неактивного типа ресурса недоступны
        user = user_factory.create_user()
        user_role = UserRole.objects.get(user=user, is_active=True).role
        # Пытаемся получить разрешения для неактивного типа ресурса
        permission = RolePermission.objects.filter(
            role=user_role,
            resource_type=resource_type
        ).first()
        # Разрешения должны существовать, но ресурс неактивен
        assert permission is not None
        assert permission.resource_type.is_active is False

    @pytest.mark.django_db
    def test_cross_resource_permission_inheritance(self, user_factory):
        """Тест независимости разрешений между разными типами ресурсов."""
        # Создаем пользователя с ролью 'user'
        user = user_factory.create_user()
        user_role = UserRole.objects.get(user=user, is_active=True).role
        # Настраиваем разные разрешения для разных типов ресурсов
        # Product - только чтение для обычного пользователя
        product_permission = RolePermission.objects.get(
            role=user_role,
            resource_type=self.product_type
        )
        product_permission.can_create = False
        product_permission.can_update = False
        product_permission.can_delete = False
        product_permission.save()

        # Order - создание заказа, редактирование и чтение только своих заказов
        order_permission = RolePermission.objects.get(
            role=user_role,
            resource_type=self.order_type
        )
        order_permission.can_create = True
        order_permission.can_update = True
        order_permission.can_delete = False
        order_permission.save()

        # Проверяем что разрешения работают независимо
        assert can_user_access_resource(user, self.product_type, 'create') is False
        assert can_user_access_resource(user, self.product_type, 'update') is False
        assert can_user_access_resource(user, self.product_type, 'delete') is False
        assert can_user_access_resource(user, self.product_type, 'read') is True
        
        assert can_user_access_resource(user, self.order_type, 'create') is True
        assert can_user_access_resource(user, self.order_type, 'update') is False
        assert can_user_access_resource(user, self.order_type, 'delete') is False
        assert can_user_access_resource(user, self.order_type, 'read') is True   # По умолчанию True
        
       # Создаем заказ, принадлежащий пользователю
        order_resource = self.create_resource('My Order', resource_type=self.order_type, owner=user)
        # Теперь может редактировать свой заказ
        assert can_user_access_resource(
            user, self.order_type, 'update', order_resource.owner
        ) is True

        assert can_user_access_resource(user, self.order_type, 'read') is True
        assert can_user_access_resource(user, self.user_resource_type, 'read') is True


    @pytest.mark.django_db
    def test_correct_permission_model(self, user_factory):
        """Тест правильной модели разрешений для разных ролей."""
        # Создаем пользователей с разными ролями
        admin_user = user_factory.create_user()
        manager_user = user_factory.create_user()
        regular_user = user_factory.create_user()

        # Назначаем роли
        admin_role = Role.objects.get(name='admin')
        manager_role = Role.objects.get(name='manager')
        user_role = Role.objects.get(name='user')

        # Удаляем автоматически назначенные роли для админа и менеджера
        UserRole.objects.filter(user__in=[admin_user, manager_user]).delete()

        # Назначаем роли
        UserRole.objects.create(user=admin_user, role=admin_role, assigned_by=admin_user)
        UserRole.objects.create(user=manager_user, role=manager_role, assigned_by=admin_user)

        # Настраиваем разрешения через базовый метод
        self.setup_permissions(
            admin_role,
            can_create=True,
            can_update=True,
            can_delete=True,
            can_manage_others=True
        )

        self.setup_permissions(
            manager_role,
            can_create=True,
            can_update=True,
            can_delete=False,
            can_manage_others=False
        )
        # Настраиваем специальные разрешения для обычного пользователя
        # Product - только чтение
        product_permission = RolePermission.objects.get(
            role=user_role,
            resource_type=self.product_type
        )
        product_permission.can_create = False
        product_permission.can_update = False
        product_permission.can_delete = False
        product_permission.save()

        # Order - может создавать и редактировать свои
        order_permission = RolePermission.objects.get(
            role=user_role,
            resource_type=self.order_type
        )
        order_permission.can_create = True
        order_permission.can_update = True
        order_permission.can_delete = False
        order_permission.save()

        # Создаем тестовые ресурсы
        admin_product = self.create_resource('Admin Product', owner=admin_user)
        manager_product = self.create_resource(
            'Manager Product', owner=manager_user
        )
        user_order = self.create_resource(
            'User Order', resource_type=self.order_type, owner=regular_user
        )

        # Проверяем права админа (полный доступ ко всему)
        assert can_user_access_resource(admin_user, self.product_type, 'create') is True
        assert can_user_access_resource(admin_user, self.product_type, 'update') is True
        assert can_user_access_resource(admin_user, self.product_type, 'read') is True
        assert can_user_access_resource(admin_user, self.product_type, 'delete') is True

        # Проверяем права менеджера
        assert can_user_access_resource(manager_user, self.product_type, 'create') is True
        assert can_user_access_resource(manager_user, self.product_type, 'read') is True
        # Может редактировать только свои продукты
        assert can_user_access_resource(
            manager_user, self.product_type, 'update', manager_product.owner
        ) is True
        assert can_user_access_resource(
            manager_user, self.product_type, 'update', admin_product.owner
        ) is False

        # Проверяем права обычного пользователя
        assert can_user_access_resource(regular_user, self.product_type, 'create') is False
        assert can_user_access_resource(regular_user, self.product_type, 'read') is True
        assert can_user_access_resource(regular_user, self.product_type, 'update') is False

        # Может редактировать только свои заказы
        assert can_user_access_resource(
            regular_user, self.order_type, 'update', user_order.owner
        ) is True
        assert can_user_access_resource(
            regular_user, self.order_type, 'update', manager_user
        ) is False
