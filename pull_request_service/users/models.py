from django.contrib.auth.models import AbstractUser
from django.db import models
from teams.models import Team


class MyUser(AbstractUser):
    pass


class User(models.Model):
    """Пользователь."""

    username = models.CharField(
        max_length=128, verbose_name="Имя пользователя")
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        verbose_name="Команда пользователя",
        related_name='members',
        blank=True,
    )
    is_active = models.BooleanField(
        default=True, verbose_name="Статус активности")

    def __str__(self):
        return self.username
