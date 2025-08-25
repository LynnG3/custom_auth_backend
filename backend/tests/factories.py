import uuid
from dataclasses import dataclass
from faker import Faker
from users.models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken

fake = Faker('ru_RU')


@dataclass
class UserFactory:
    """Фабрика для создания тестовых пользователей."""

    password: str = "TestPass123!"
    password_confirm: str = "TestPass123!"
    first_name: str = None
    last_name: str = None

    def __post_init__(self):
        if self.first_name is None:
            self.first_name = fake.first_name()
        if self.last_name is None:
            self.last_name = fake.last_name()

    def create_user(self, **kwargs) -> CustomUser:
        """Создает пользователя в базе данных."""
        email = f"user_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            'email': email,
            'first_name': self.first_name,
            'last_name': self.last_name,
        }
        user_data.update(kwargs)

        user = CustomUser.objects.create_user(
            email=user_data['email'],
            password=self.password,
            first_name=user_data['first_name'],
            last_name=user_data['last_name']
        )
        return user

    def create_admin(self, **kwargs) -> CustomUser:
        """Создает админа в базе данных."""
        email = f"user_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            'email': email,
            'first_name': self.first_name,
            'last_name': self.last_name,
        }
        user_data.update(kwargs)

        admin = CustomUser.objects.create_superuser(
            email=user_data['email'],
            password=self.password,  # Важно: передаем пароль
            first_name=user_data['first_name'],
            last_name=user_data['last_name']
        )
        return admin

    def create_user_data(self):
        """Создает данные для регистрации пользователя."""
        email = f"user_{uuid.uuid4().hex[:8]}@example.com"
        return {
            'email': email,
            'password': self.password,
            'password_confirm': self.password_confirm,
            'first_name': self.first_name,
            'last_name': self.last_name,
        }


@dataclass
class AuthFactory:
    """Фабрика для аутентификации."""

    @staticmethod
    def get_auth_headers(user):
        """Получает заголовки аутентификации для пользователя."""
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}
