from django.conf import settings
from django.core.cache import cache
from rest_framework import authentication
import jwt

from .models import CustomUser


class CustomJWTAuthentication(authentication.BaseAuthentication):
    """Кастомный класс аутентификации для JWT токенов."""

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        # Проверяем, не отозван ли токен
        if cache.get(f'revoked_token_{token}'):
            return None

        try:
            # Декодируем JWT токен
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')

            if user_id:
                user = CustomUser.objects.get(id=user_id, is_active=True)
                return (user, token)
        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, CustomUser.DoesNotExist):
            pass

        return None

    def authenticate_header(self, request):
        return 'Bearer'
