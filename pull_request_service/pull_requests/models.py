from django.db import models
from users.models import User


STATUS_CHOICES = (
    ('OPEN', 'Open'),
    ('MERGED', 'Merged'),
)


class PullRequest(models.Model):
    """Pull Request."""

    pull_request_name = models.CharField(
        max_length=128, verbose_name="Название")
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name='requests'
    )
    status = models.CharField(
        max_length=6,
        choices=STATUS_CHOICES,
        verbose_name="Статус"
    )
    assigned_reviewers = models.ManyToManyField(
        User,
        related_name='review_assignments',
        blank=True,
        verbose_name="Ревьюверы"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время создания"
    )
    merged_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Дата и время слияния"
    )

    def __str__(self):
        return self.pull_request_name
