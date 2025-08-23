import logging

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from drf_spectacular.utils import extend_schema
import jwt

from .models import CustomUser
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    UserUpdateSerializer, ChangePasswordSerializer
)

logger = logging.getLogger('auth_system')


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для управления пользователями."""

    queryset = CustomUser.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """Установка разрешений в зависимости от действия."""
        if self.action in ['register', 'login']:
            return [AllowAny()]
        elif self.action in ['list', 'retrieve']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    @extend_schema(
        tags=['authentication'],
        summary='Регистрация пользователя',
        description='Создание нового пользователя в системе'
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Регистрация пользователя."""
        logger.info(f"Попытка регистрации пользователя: {request.data.get('email')}")

        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"Пользователь успешно зарегистрирован: {user.email}")

            # Создаем JWT токен
            token = self._create_jwt_token(user)

            return Response({
                'message': 'Пользователь успешно зарегистрирован',
                'user': UserSerializer(user).data,
                'token': token
            }, status=status.HTTP_201_CREATED)

        logger.warning(f"Ошибка регистрации: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['authentication'],
        summary='Вход пользователя',
        description='Аутентификация пользователя по email и паролю'
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Вход пользователя в систему."""
        logger.info(f"Попытка входа пользователя: {request.data.get('email')}")

        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            user = authenticate(request, username=email, password=password)

            if user and user.is_active:
                logger.info(f"Пользователь успешно вошел: {user.email}")

                # Создаем JWT токен
                token = self._create_jwt_token(user)

                return Response({
                    'message': 'Успешный вход',
                    'user': UserSerializer(user).data,
                    'token': token
                })
            else:
                logger.warning(f"Неудачная попытка входа: {email}")
                return Response({
                    'error': 'Неверные учетные данные или аккаунт неактивен'
                }, status=status.HTTP_401_UNAUTHORIZED)

        logger.warning(f"Ошибка входа: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['authentication'],
        summary='Выход пользователя',
        description='Выход пользователя из системы'
    )
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Выход пользователя из системы."""
        logger.info(f"Пользователь вышел из системы: {request.user.email}")

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

            # Добавляем токен в черный список (кэш)
            cache.set(f'revoked_token_{token}', True, timeout=86400)  # 24 часа

            logger.info(f"Пользователь вышел из системы: {request.user.email}")
            return Response({'message': 'Успешный выход из системы'})

        return Response(
            {'error': 'Токен не найден'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        tags=['profile management'],
        summary='Информация о пользователе',
        description='Получение данных текущего аутентифицированного пользователя'
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Получение информации о текущем пользователе."""
        logger.debug(f"Запрос информации о пользователе: {request.user.email}")

        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        tags=['profile management'],
        summary='Информация о пользователе',
        description='Обновление информации о пользователе'
    )
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Обновление профиля пользователя."""
        logger.info(f"Обновление профиля пользователя: {request.user.email}")

        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Профиль пользователя обновлен: {request.user.email}")
            return Response(UserSerializer(request.user).data)

        logger.warning(f"Ошибка обновления профиля: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['Profile Management'],
        summary='Информация о пользователе',
        description='Обновление пароля пользователя'
    )
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Смена пароля пользователя."""
        logger.info(f"Попытка смены пароля пользователя: {request.user.email}")

        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            logger.info(f"Пароль пользователя изменен: {user.email}")
            return Response({'message': 'Пароль успешно изменен'})

        logger.warning(f"Ошибка смены пароля: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['account management'],
        summary='Информация о пользователе',
        description='Мягкое удаление аккаунта пользователя'
    )
    @action(detail=False, methods=['post'])
    def delete_account(self, request):
        """Мягкое удаление аккаунта."""
        logger.info(f"Попытка удаления аккаунта пользователя: {request.user.email}")

        user = request.user
        user.soft_delete()

        logger.info(f"Аккаунт пользователя удален: {user.email}")
        return Response({'message': 'Аккаунт успешно удален'})

    def _create_jwt_token(self, user):
        """Создание JWT токена."""
        payload = {
            'user_id': user.id,
            'email': user.email,
            'exp': timezone.now() + timezone.timedelta(days=1),  # Токен на 1 день
            'iat': timezone.now()
        }

        # Временно используем SECRET_KEY, позже вынесем в переменные окружения
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        return token
