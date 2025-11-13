from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TeamViewSet, UserViewSet

router = DefaultRouter()
router.register(r'team', TeamViewSet)
router.register(r'users', UserViewSet)
router.register(r'pullRequest', UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
]