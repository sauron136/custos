from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .permissions import IsOwnerPermission
from .models import Task, Project, Context, Tag
from .serializers import TaskSerializer, ProjectSerializer, ContextSerializer, TagSerializer

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsOwnerPermission]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def perform_create(self):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def high_priority(self, request):
        high_priority_tasks = self.get_queryset().filter(priority__gte=3)
        serializer = self.get_serializer(high_priority_tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_complete(self, request):
        task_ids = request.data.get('task_ids', [])

        if not task_ids:
            return Response({'error': 'No task IDs provided'}, status=400)

        tasks = self.get_queryset().filter(
            id__in=task_ids,
            status__in=['inbox', 'next', 'waiting', 'someday']
         )

        completed_count = 0
        for task in tasks:
            task.mark_complete()
            completed_count += 1

        return Response({
            'message': f'{completed_count} tasks marked as complete',
            'completed_tasks': completed_count
            })

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsOwnerPermission]

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ContextViewSet(viewsets.ModelViewSet):
    serializer_class = ContextSerializer
    permission_classes = [IsOwnerPermission]

    def get_queryset(self):
        return Context.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated, IsOwnerPermission]

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
