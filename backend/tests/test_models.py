import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from faker import Faker


User = get_user_model()
fake = Faker('ru_RU')


class TestCustomUserModel:
    """Тесты для модели CustomUser."""

    @pytest.mark.django_db
    def test_custom_user_creation(self, user_factory):
        """Тест создания пользователя."""
        user = user_factory.create_user()

        assert user.email is not None
        assert user.first_name == user_factory.first_name
        assert user.last_name == user_factory.last_name
        assert user.username is None
        assert user.is_verified is False
        assert user.is_active is True

        # Очистка
        user.delete()

    @pytest.mark.django_db
    def test_custom_user_manager_create_user(self, user_factory):
        """Тест менеджера для создания обычного пользователя."""
        user = user_factory.create_user()

        assert user.email is not None
        assert user.check_password(user_factory.password)
        assert user.is_superuser is False
        assert user.is_staff is False

        # Очистка
        user.delete()

    @pytest.mark.django_db
    def test_custom_user_manager_create_superuser(self, user_factory):
        """Тест менеджера для создания суперпользователя."""
        admin = user_factory.create_admin()

        assert admin.email is not None
        assert admin.is_superuser is True
        assert admin.is_staff is True
        assert admin.is_verified is True

        # Очистка
        admin.delete()

    @pytest.mark.django_db
    def test_custom_user_soft_delete(self, user_factory):
        """Тест мягкого удаления пользователя."""
        user = user_factory.create_user()

        # Мягкое удаление
        user.soft_delete()

        assert user.is_active is False
        assert user.deleted_at is not None

    @pytest.mark.django_db
    def test_custom_user_full_name_property(self, user_factory):
        """Тест свойства full_name."""
        user = user_factory.create_user(
            first_name='Иван',
            last_name='Иванов'
        )

        assert user.full_name == 'Иванов Иван'

        # Очистка
        user.delete()

    @pytest.mark.django_db
    def test_custom_user_password_hashing(self, user_factory):
        """Тест хеширования пароля."""
        user = user_factory.create_user()
        test_password = 'TestPassword123!'

        # Устанавливаем пароль
        user.set_password(test_password)
        user.save()

        # Проверяем, что пароль хешируется
        assert user.password != test_password

        # Проверяем, что пароль проверяется корректно
        assert user.check_password(test_password)
        assert not user.check_password('WrongPassword123!')

        # Очистка
        user.delete()

    @pytest.mark.django_db
    def test_custom_user_required_fields(self, user_factory):
        """Тест обязательных полей (email)."""
        #  попытка создать пользователя без email
        with pytest.raises(ValueError):
            user_factory.create_user(email='')

    @pytest.mark.django_db(transaction=True)
    def test_custom_user_unique_email(self, user_factory):
        """Тест уникальности email."""

        user1 = user_factory.create_user()
        with pytest.raises(IntegrityError):
            user_factory.create_user(email=user1.email)
        user1.delete()
