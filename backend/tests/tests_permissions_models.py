import pytest
from faker import Faker

from permissions.models import Role, UserRole, RolePermission

fake = Faker('ru_RU')


class TestRoleModel:
    """Тесты для модели Role."""
    
    @pytest.mark.django_db
    def test_role_creation(self):
        """Тест создания роли."""
        role = Role.objects.create(
            name='test_role',
            description='Тестовая роль',
            is_default=False
        )
        
        assert role.name == 'test_role'
        assert role.description == 'Тестовая роль'
        assert role.is_default is False
        assert role.created_at is not None
        assert role.updated_at is not None
    
    @pytest.mark.django_db
    def test_role_str_representation(self):
        """Тест строкового представления роли."""
        role = Role.objects.create(
            name='admin',
            description='Администратор'
        )
        
        assert str(role) == 'admin'
    
    @pytest.mark.django_db
    def test_role_choices(self):
        """Тест валидных значений для поля name."""
        valid_names = ['admin', 'manager', 'user', 'guest']
        
        for name in valid_names:
            role = Role.objects.create(name=name, description=f'Роль {name}')
            assert role.name in valid_names


class TestUserRoleModel:
    """Тесты для модели UserRole."""
    
    @pytest.mark.django_db
    def test_user_role_creation(self, user_factory):
        """Тест создания связи пользователь-роль."""
        user = user_factory.create_user()
        role = Role.objects.create(name='test_role', description='Тестовая роль')
        
        user_role = UserRole.objects.create(
            user=user,
            role=role,
            assigned_by=user,
            is_active=True
        )
        
        assert user_role.user == user
        assert user_role.role == role
        assert user_role.assigned_by == user
        assert user_role.is_active is True
        assert user_role.assigned_at is not None
    
    @pytest.mark.django_db
    def test_user_role_unique_constraint(self, user_factory):
        """Тест уникальности связи пользователь-роль."""
        user = user_factory.create_user()
        role = Role.objects.create(name='test_role', description='Тестовая роль')
        
        # Создаем первую связь
        UserRole.objects.create(
            user=user,
            role=role,
            assigned_by=user
        )
        
        # Пытаемся создать дублирующую связь
        with pytest.raises(Exception):  # IntegrityError или ValidationError
            UserRole.objects.create(
                user=user,
                role=role,
                assigned_by=user
            )
    
    @pytest.mark.django_db
    def test_user_role_str_representation(self, user_factory):
        """Тест строкового представления связи пользователь-роль."""
        user = user_factory.create_user()
        role = Role.objects.create(name='admin', description='Администратор')
        
        user_role = UserRole.objects.create(
            user=user,
            role=role,
            assigned_by=user
        )
        
        expected_str = f"{user.email} - {role.name}"
        assert str(user_role) == expected_str


class TestResourcePermissionModel:
    """Тесты для модели ResourcePermission."""
    
    @pytest.mark.django_db
    def test_resource_permission_creation(self):
        """Тест создания разрешения на ресурс."""
        role = Role.objects.create(name='test_role', description='Тестовая роль')
        
        permission = ResourcePermission.objects.create(
            role=role,
            resource_name='users',
            resource_type='module',
            read_permission=True,
            create_permission=False
        )
        
        assert permission.role == role
        assert permission.resource_name == 'users'
        assert permission.resource_type == 'module'
        assert permission.read_permission is True
        assert permission.create_permission is False
    
    @pytest.mark.django_db
    def test_resource_permission_unique_constraint(self):
        """Тест уникальности разрешения на ресурс."""
        role = Role.objects.create(name='test_role', description='Тестовая роль')
        
        # Создаем первое разрешение
        ResourcePermission.objects.create(
            role=role,
            resource_name='users',
            resource_type='module'
        )
        
        # Пытаемся создать дублирующее разрешение
        with pytest.raises(Exception):  # IntegrityError или ValidationError
            ResourcePermission.objects.create(
                role=role,
                resource_name='users',
                resource_type='module'
            )
    
    @pytest.mark.django_db
    def test_resource_permission_str_representation(self):
        """Тест строкового представления разрешения."""
        role = Role.objects.create(name='admin', description='Администратор')
        
        permission = ResourcePermission.objects.create(
            role=role,
            resource_name='users',
            resource_type='module'
        )
        
        expected_str = f"{role.name} - Пользователи"
        assert str(permission) == expected_str