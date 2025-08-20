from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import bcrypt


class CustomUserManager(BaseUserManager):
    """Кастомный менеджер для создания пользователей."""

    def create_user(self, email, password=None, **extra_fields):
        """Создание обычного пользователя. """
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Создание суперпользователя. """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Кастомная модель пользователя."""

    # Вместо username используем email для входа
    username = None

    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    is_verified = models.BooleanField(
        default=False, verbose_name='Подтвержден'
    )
    deleted_at = models.DateTimeField(
        null=True, blank=True, verbose_name='Дата удаления'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()
    class Meta:

        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'users'

    def __str__(self):
        return self.email

    def soft_delete(self):
        """Мягкое удаление пользователя."""
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save()

    def set_password(self, raw_password):
        """Хеширование пароля с помощью bcrypt."""
        if isinstance(raw_password, str):
            raw_password = raw_password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password = bcrypt.hashpw(raw_password, salt).decode('utf-8')

    def check_password(self, raw_password):
        """Проверка пароля."""
        if isinstance(raw_password, str):
            raw_password = raw_password.encode('utf-8')
        return bcrypt.checkpw(raw_password, self.password.encode('utf-8'))

    @property
    def full_name(self):
        """Полное имя пользователя."""
        return f"{self.last_name} {self.first_name}"
