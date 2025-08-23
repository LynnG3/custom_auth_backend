from django.db import models

from permissions.constants import RESOURCE_TYPES
from users.models import CustomUser


class Resource(models.Model):
    """Ресурсы системы."""

    name = models.CharField(
        max_length=100,
        verbose_name='Название ресурса'
    )
    resource_type = models.CharField(
        max_length=20,
        choices=RESOURCE_TYPES,
        verbose_name='Тип ресурса'
    )
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Владелец',
        null=True, 
        blank=True
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
        return f"{self.name} ({self.resource_type})"
