import pytest
from django.urls import reverse
from rest_framework import status
from faker import Faker

from users.models import CustomUser


fake = Faker('ru_RU')


class TestUserRegistration:
    """Тесты для регистрации пользователей."""

    @pytest.mark.django_db
    def test_user_registration_success(self, api_client, user_data_factory):
        """Тест успешной регистрации пользователя."""
        user_data = user_data_factory

        url = reverse('users:user-register')
        response = api_client.post(url, user_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert 'token' in response.data
        assert 'user' in response.data
        assert response.data['message'] == 'Пользователь успешно зарегистрирован'

        # Проверяем, что пользователь создан в базе
        user = CustomUser.objects.get(email=user_data['email'])
        assert user.first_name == user_data['first_name']
        assert user.last_name == user_data['last_name']
        assert user.is_verified is False  # По умолчанию не подтвержден

    @pytest.mark.django_db
    def test_user_registration_password_mismatch(
        self,
        api_client,
        user_data_factory
    ):
        """Тест регистрации с несовпадающими паролями."""
        user_data = user_data_factory.copy()
        user_data['password_confirm'] = 'DifferentPass123!'

        url = reverse('users:user-register')
        response = api_client.post(url, user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data
        assert 'Пароли не совпадают' in str(response.data['non_field_errors'])

    @pytest.mark.django_db
    def test_user_registration_duplicate_email(self, api_client, user_data_factory):
        """Тест регистрации с существующим email."""
        user_data = user_data_factory
        url = reverse('users:user-register')
        response = api_client.post(url, user_data)
        assert response.status_code == status.HTTP_201_CREATED

        # Пытаемся зарегистрировать второго с тем же email
        duplicate_data = user_data_factory.copy()
        duplicate_data['email'] = user_data['email']  # Тот же email

        response = api_client.post(url, duplicate_data)

        # Проверяем, что API возвращает ошибку 400
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data  # Поле с ошибкой

        # Очистка
        user = CustomUser.objects.get(email=user_data['email'])
        user.delete()


class TestUserLogin:
    """Тесты для входа пользователей."""

    @pytest.mark.django_db
    def test_user_login_success(self, api_client, user):
        """Тест успешного входа зарегистрированного пользователя."""
        login_data = {
            'email': user.email,
            'password': 'TestPass123!'
        }

        url = reverse('users:user-login')
        response = api_client.post(url, login_data)

        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data
        assert 'user' in response.data
        assert response.data['message'] == 'Успешный вход'

    @pytest.mark.django_db
    def test_user_login_unregistered_user(self, api_client):
        """Тест входа незарегистрированного пользователя."""
        login_data = {
            'email': 'nonexistent@test.com',
            'password': 'TestPass123!'
        }

        url = reverse('users:user-login')
        response = api_client.post(url, login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'error' in response.data
        assert 'Неверные учетные данные или аккаунт неактивен' in response.data['error']

    @pytest.mark.django_db
    def test_user_login_wrong_password(self, api_client, user):
        """Тест входа с неверным паролем."""
        login_data = {
            'email': user.email,
            'password': 'WrongPass123!'
        }

        url = reverse('users:user-login')
        response = api_client.post(url, login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'error' in response.data
        assert 'Неверные учетные данные или аккаунт неактивен' in response.data['error']


class TestUserLogout:
    """Тесты для выхода пользователей."""

    @pytest.mark.django_db
    def test_user_logout_success(self, authenticated_client):
        """Тест успешного выхода залогиненного пользователя."""
        url = reverse('users:user-logout')
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Успешный выход из системы'

    @pytest.mark.django_db
    def test_user_logout_unauthenticated(self, api_client):
        """Тест выхода неаутентифицированного пользователя."""
        url = reverse('users:user-logout')
        response = api_client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUserProfile:
    """Тесты для управления профилем пользователя."""

    @pytest.mark.django_db
    def test_get_user_profile(self, authenticated_client, user):
        """Тест получения профиля залогиненного пользователя."""
        url = reverse('users:user-me')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email
        assert response.data['first_name'] == user.first_name
        assert response.data['last_name'] == user.last_name

    @pytest.mark.django_db
    def test_update_user_profile(self, authenticated_client, user):
        """Тест обновления профиля пользователя."""
        new_last_name = fake.last_name()
        update_data = {'last_name': new_last_name}

        url = reverse('users:user-profile')
        response = authenticated_client.put(url, update_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['last_name'] == new_last_name

        # Проверяем, что изменения сохранились в базе
        user.refresh_from_db()
        assert user.last_name == new_last_name

    @pytest.mark.django_db
    def test_change_user_password(self, authenticated_client, user):
        """Тест смены пароля пользователя."""
        old_password = 'TestPass123!'
        new_password = 'NewPass123!'

        change_data = {
            'old_password': old_password,
            'new_password': new_password,
            'new_password_confirm': new_password
        }

        url = reverse('users:user-change-password')
        response = authenticated_client.post(url, change_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Пароль успешно изменен'

        # Проверяем, что новый пароль работает
        user.refresh_from_db()  # Обновляем объект из базы
        assert user.check_password(new_password)

    @pytest.mark.django_db
    def test_change_password_wrong_old_password(self, authenticated_client):
        """Тест смены пароля с неверным старым паролем."""
        change_data = {
            'old_password': 'WrongOldPass123!',
            'new_password': 'NewPass123!',
            'new_password_confirm': 'NewPass123!'
        }

        url = reverse('users:user-change-password')
        response = authenticated_client.post(url, change_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'old_password' in response.data


class TestAdminOperations:
    """Тесты для админских операций."""

    @pytest.mark.django_db
    def test_admin_get_users_list(self, admin_client, user_factory):
        """Тест получения списка пользователей админом."""
        # Создаем несколько тестовых пользователей
        users = []
        for _ in range(3):
            # Создаем НОВУЮ фабрику для каждого пользователя
            new_factory = user_factory
            users.append(new_factory.create_user())

        url = reverse('users:user-list')
        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data or 'count' in response.data

        # Проверяем, что все пользователи в списке
        user_emails = [user['email'] for user in response.data.get('results', response.data)]
        for user in users:
            assert user.email in user_emails

        # Очистка
        for user in users:
            user.delete()

    @pytest.mark.django_db
    def test_admin_get_user_detail(self, admin_client, user_factory):
        """Тест получения информации о конкретном пользователе админом."""
        user = user_factory.create_user()

        url = reverse('users:user-detail', kwargs={'pk': user.pk})
        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email
        assert response.data['first_name'] == user.first_name
        assert response.data['last_name'] == user.last_name

    @pytest.mark.django_db
    def test_regular_user_cannot_get_users_list(self, authenticated_client):
        """Тест что обычный пользователь не может получить список пользователей."""
        url = reverse('users:user-list')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUserAccountManagement:
    """Тесты для управления аккаунтом пользователя."""

    @pytest.mark.django_db
    def test_user_delete_account(self, authenticated_client, user):
        """Тест мягкого удаления аккаунта пользователя."""
        url = reverse('users:user-delete-account')
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Аккаунт успешно удален'

        # Проверяем, что пользователь помечен как неактивный
        user.refresh_from_db()
        assert user.is_active is False
        assert user.deleted_at is not None


class TestJWTToken:
    """Тесты для JWT токенов."""

    @pytest.mark.django_db
    def test_jwt_token_creation_on_login(self, api_client, user):
        """Тест создания JWT токена при входе."""
        login_data = {
            'email': user.email,
            'password': 'TestPass123!'
        }

        url = reverse('users:user-login')
        response = api_client.post(url, login_data)

        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data

        # Проверяем, что токен валидный
        token = response.data['token']
        assert len(token) > 0

        # Проверяем, что токен можно использовать для аутентификации
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        profile_url = reverse('users:user-me')
        profile_response = api_client.get(profile_url)

        assert profile_response.status_code == status.HTTP_200_OK
