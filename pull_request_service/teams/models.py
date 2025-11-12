from django.db import models


class Team(models.Model):
    """Команда."""

    team_name = models.CharField(max_length=128, unique=True,
                                 verbose_name="Название")

    def __str__(self):
        return self.team_name
