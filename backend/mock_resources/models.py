from django.db import models
from django.core.exceptions import ValidationError

from users.models import CustomUser
from permissions.models import ResourceType


class Resource(models.Model):
    """Ресурсы системы с динамическими типами."""

    name = models.CharField(
        max_length=100,
        verbose_name='Название ресурса'
    )
    resource_type = models.ForeignKey(
        ResourceType,
        on_delete=models.CASCADE,
        verbose_name='Тип ресурса',
        related_name='resources'
    )
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Владелец',
        null=True,
        blank=True,
        related_name='owned_resources'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Ресурс'
        verbose_name_plural = 'Ресурсы'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.resource_type.name})"

    def clean(self):
        """Валидация: ресурс должен быть активным."""
        if self.resource_type and not self.resource_type.is_active:
            raise ValidationError(
                f"Нельзя создать ресурс типа '{self.resource_type.name}' - тип неактивен"
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
