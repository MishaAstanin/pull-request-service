from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PullRequestViewSet,
    TeamViewSet,
    UserViewSet,
    get_pr_statistics,
    get_user_statistics,
)


router = DefaultRouter()
router.register(r'team', TeamViewSet)
router.register(r'users', UserViewSet)
router.register(r'pullRequest', PullRequestViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path('statisticsUser/', get_user_statistics),
    path('statisticsPR/', get_pr_statistics),
]
