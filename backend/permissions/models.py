from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .constants import RESOURCE_TYPES
from users.models import CustomUser

User = get_user_model()


class Role(models.Model):
    """Модель ролей пользователей."""

    name = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Название роли'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание роли'
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name='Роль по умолчанию'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        """Валидация: только одна роль может быть по умолчанию."""
        if self.is_default:
            Role.objects.filter(
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class UserRole(models.Model):
    """Связь пользователей с ролями."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        verbose_name='Роль'
    )
    assigned_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True, 
        related_name='assigned_roles',
        verbose_name='Назначил'
    )
    assigned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата назначения'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна'
    )

    class Meta:
        verbose_name = 'Роль пользователя'
        verbose_name_plural = 'Роли пользователей'
        unique_together = ['user', 'role']
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.user.email} - {self.role.name}"


class RolePermission(models.Model):
    """Разрешения ролей на ресурсы."""

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        verbose_name='Роль'
    )
    resource_type = models.CharField(
        max_length=20, 
        choices=RESOURCE_TYPES,
        verbose_name='Тип ресурса'
    )
    
    # Права на ресурсы
    can_create = models.BooleanField(default=False, verbose_name='Может создавать')
    can_read = models.BooleanField(default=False, verbose_name='Может читать')
    can_update = models.BooleanField(default=False, verbose_name='Может обновлять')
    can_delete = models.BooleanField(default=False, verbose_name='Может удалять')
    can_manage_others = models.BooleanField(default=False, verbose_name='Может управлять чужими')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Разрешение роли'
        verbose_name_plural = 'Разрешения ролей'
        unique_together = ['role', 'resource_type']
        ordering = ['role__name', 'resource_type']
    
    def __str__(self):
        return f"{self.role.name} - {self.resource_type}"
    
    def clean(self):
        """Валидация: логика наследования прав."""
        # Если можно управлять чужими, то должны быть базовые права
        if self.can_manage_others:
            if not self.can_read:
                self.can_read = True
            if not self.can_update and not self.can_delete:
                # Должно быть хотя бы одно право на управление
                if not self.can_update:
                    self.can_update = True
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


# Сигналы для автоматического назначения ролей
@receiver(post_save, sender=User)
def create_default_role_for_user(sender, instance, created, **kwargs):
    """Автоматически назначает роль 'user'
    новым зарегистрированным пользователям."""
    if created:
        if not UserRole.objects.filter(user=instance).exists():
            user_role, _ = Role.objects.get_or_create(
                name='user',
                defaults={
                    'description': 'Обычный пользователь системы',
                    'is_default': False
                }
            )
            UserRole.objects.create(
                user=instance,
                role=user_role,
                assigned_by=instance,
                is_active=True
            )


@receiver(post_save, sender=Role)
def create_default_permissions_for_role(sender, instance, created, **kwargs):
    """Автоматически создает базовые разрешения для новых ролей."""
    if created:
        # Создаем базовые разрешения для всех типов ресурсов
        for resource_type, _ in RESOURCE_TYPES:
            # Используем get_or_create чтобы избежать дублирования
            RolePermission.objects.get_or_create(
                role=instance,
                resource_type=resource_type,
                defaults={
                    'can_read': True,  # Все роли могут читать
                    'can_create': False,
                    'can_update': False,
                    'can_delete': False,
                    'can_manage_others': False
                }
            )
