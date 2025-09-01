from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet, CategoryViewSet, TagViewSet,
    TaskViewSet, SubtaskViewSet, TaskAttachmentViewSet, TaskCommentViewSet,
    TimeEntryViewSet, NotificationViewSet
)

# Main router
router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='projects')
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'tasks', TaskViewSet, basename='tasks')
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('', include(router.urls)),
]
