import pytest
from faker import Faker

from permissions.models import (
    Role, UserRole, RolePermission, ResourceType
)

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

    @pytest.mark.django_db
    def test_role_str_representation(self):
        """Тест строкового представления роли."""
        role = Role.objects.create(
            name='admin',
            description='Администратор'
        )

        assert str(role) == 'admin'

    @pytest.mark.django_db
    def test_role_default_validation(self):
        """Тест валидации роли по умолчанию."""
        # Создаем первую роль по умолчанию
        role1 = Role.objects.create(
            name='default_role1',
            description='Первая роль по умолчанию',
            is_default=True
        )

        # Создаем вторую роль по умолчанию - первая должна стать не по умолчанию
        role2 = Role.objects.create(
            name='default_role2',
            description='Вторая роль по умолчанию',
            is_default=True
        )

        # Обновляем из базы
        role1.refresh_from_db()
        role2.refresh_from_db()

        assert role1.is_default is False
        assert role2.is_default is True


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


class TestRolePermissionModel:
    """Тесты для модели RolePermission."""

    @pytest.mark.django_db
    def test_role_permission_creation(self):
        """Тест создания разрешения роли на ресурс."""
        role = Role.objects.create(name='test_role', description='Тестовая роль')
        resource_type = ResourceType.objects.create(
            name='test_resource'
        )

        # Сигнал автоматически создал разрешение, поэтому получаем существующее
        permission = RolePermission.objects.get(
            role=role,
            resource_type=resource_type
        )

        assert permission.role == role
        assert permission.resource_type == resource_type
        assert permission.can_read is True  # По умолчанию True
        assert permission.can_create is False  # По умолчанию False
        assert permission.can_update is False  # По умолчанию False
        assert permission.can_delete is False  # По умолчанию False
        assert permission.can_manage_others is False  # По умолчанию False

    @pytest.mark.django_db
    def test_role_permission_unique_constraint(self):
        """Тест уникальности разрешения роли на ресурс."""
        role = Role.objects.create(name='test_role', description='Тестовая роль')
        resource_type = ResourceType.objects.create(
            name='test_resource'
        )

        # Сигнал автоматически создал разрешение
        permission1 = RolePermission.objects.get(
            role=role,
            resource_type=resource_type
        )

        # Пытаемся создать дублирующее разрешение
        with pytest.raises(Exception):  # IntegrityError или ValidationError
            RolePermission.objects.create(
                role=role,
                resource_type=resource_type
            )

    @pytest.mark.django_db
    def test_role_permission_str_representation(self):
        """Тест строкового представления разрешения."""
        role = Role.objects.create(name='admin', description='Администратор')
        resource_type = ResourceType.objects.create(
            name='users'
        )

        # Сигнал автоматически создал разрешение
        permission = RolePermission.objects.get(
            role=role,
            resource_type=resource_type
        )

        expected_str = f"{role.name} - {resource_type.name}"
        assert str(permission) == expected_str

    @pytest.mark.django_db
    def test_role_permission_validation_logic(self):
        """Тест логики валидации разрешений."""
        role = Role.objects.create(name='test_role', description='Тестовая роль')
        resource_type = ResourceType.objects.create(
            name='test_resource'
        )

        # Сигнал автоматически создал разрешение
        permission = RolePermission.objects.get(
            role=role,
            resource_type=resource_type
        )

        # Изменяем разрешение с can_manage_others=True
        permission.can_manage_others = True
        permission.can_read = False  # Должно стать True
        permission.can_update = False  # Должно стать True
        permission.save()

        # Проверяем что логика валидации сработала
        permission.refresh_from_db()
        assert permission.can_read is True
        assert permission.can_update is True


class TestResourceTypeModel:
    """Тесты для модели ResourceType."""

    @pytest.mark.django_db
    def test_resource_type_creation(self):
        """Тест создания типа ресурса."""
        resource_type = ResourceType.objects.create(
            name='test_resource',
            description='Описание тестового ресурса',
            is_active=True
        )

        assert resource_type.name == 'test_resource'
        assert resource_type.description == 'Описание тестового ресурса'
        assert resource_type.is_active is True
        assert resource_type.created_at is not None

    @pytest.mark.django_db
    def test_resource_type_name_lowercase(self):
        """Тест автоматического преобразования названия в нижний регистр."""
        # Создаем объект и вызываем clean() вручную
        resource_type = ResourceType(
            name='UPPERCASE_RESOURCE',
            description='Ресурс в верхнем регистре'
        )
        resource_type.clean()  # Вызываем clean() вручную
        resource_type.save()

        assert resource_type.name == 'uppercase_resource'

    @pytest.mark.django_db
    def test_resource_type_str_representation(self):
        """Тест строкового представления типа ресурса."""
        resource_type = ResourceType.objects.create(
            name='product',
            description='Товары и услуги'
        )

        assert str(resource_type) == 'product'
