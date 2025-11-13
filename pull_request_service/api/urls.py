from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TeamViewSet, UserViewSet, PullRequestViewSet

router = DefaultRouter()
router.register(r'team', TeamViewSet)
router.register(r'users', UserViewSet)
router.register(r'pullRequest', PullRequestViewSet)

urlpatterns = [
    path("", include(router.urls)),
]