from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserProfileViewSet

# Main router
router = DefaultRouter()
router.register(r'profile', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
]
