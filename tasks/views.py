from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from django.db import transaction

from .models import (
    Project, Category, Tag, Task, Subtask, 
    TaskAttachment, TaskComment, TimeEntry, Notification,
    ProjectCollaborator
)
from .serializers import (
    ProjectSerializer, CategorySerializer, 
    TagSerializer, TaskSerializer, TaskCreateSerializer, TaskListSerializer,
    SubtaskSerializer, TaskAttachmentSerializer, TaskCommentSerializer,
    TimeEntrySerializer, NotificationSerializer, BulkTaskActionSerializer,
    TaskFilterSerializer, DashboardStatsSerializer, ProjectInviteSerializer,
    RecurringTaskSerializer
)
from .filters import TaskFilter
from django_filters.rest_framework import DjangoFilterBackend
from .permissions import IsOwnerOrReadOnly, CanEditProject


class ProjectViewSet(viewsets.ModelViewSet):
    """Project management"""
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = Project.objects.filter(
            Q(user=self.request.user) |
            Q(collaborators=self.request.user)
        ).distinct()
        
        # Filter parameters
        is_favorite = self.request.query_params.get('is_favorite')
        is_archived = self.request.query_params.get('is_archived')
        
        if is_favorite is not None:
            queryset = queryset.filter(is_favorite=is_favorite.lower() == 'true')
        
        if is_archived is not None:
            queryset = queryset.filter(is_archived=is_archived.lower() == 'true')
        else:
            queryset = queryset.filter(is_archived=False)  # Default: exclude archived
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanEditProject])
    def invite_collaborator(self, request, pk=None):
        """Invite user to collaborate on project"""
        project = self.get_object()
        serializer = ProjectInviteSerializer(data=request.data, context={'project': project})
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            role = serializer.validated_data['role']
            
            from authentication.models import User
            user = User.objects.get(email=email)
            
            # Create collaboration
            collaborator = ProjectCollaborator.objects.create(
                project=project,
                user=user,
                role=role,
                invited_by=request.user
            )
            
            # TODO: Send invitation email
            
            return Response({
                'message': f'Invitation sent to {email}',
                'collaborator_id': collaborator.id
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Toggle project favorite status"""
        project = self.get_object()
        project.is_favorite = not project.is_favorite
        project.save()
        
        return Response({
            'message': 'Favorite status updated',
            'is_favorite': project.is_favorite
        })
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive/unarchive project"""
        project = self.get_object()
        project.is_archived = not project.is_archived
        project.save()
        
        return Response({
            'message': f'Project {"archived" if project.is_archived else "unarchived"}',
            'is_archived': project.is_archived
        })


class CategoryViewSet(viewsets.ModelViewSet):
    """Category management"""
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering = ['name']
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    """Tag management"""
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering = ['name']
    
    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    """Task management with comprehensive filtering"""
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'due_date', 'priority', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Task.objects.filter(
            Q(user=self.request.user) |
            Q(assigned_to=self.request.user)
        ).filter(is_deleted=False).distinct().select_related(
            'project', 'category', 'user', 'assigned_to'
        ).prefetch_related('tags', 'subtasks')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        elif self.action == 'list':
            return TaskListSerializer
        return TaskSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark task as completed"""
        task = self.get_object()
        task.complete_task()
        
        return Response({
            'message': 'Task completed',
            'completed_at': task.completed_at
        })
    
    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """Reopen completed task"""
        task = self.get_object()
        task.reopen_task()
        
        return Response({'message': 'Task reopened'})
    
    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Toggle task favorite status"""
        task = self.get_object()
        task.is_favorite = not task.is_favorite
        task.save()
        
        return Response({
            'message': 'Favorite status updated',
            'is_favorite': task.is_favorite
        })
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on multiple tasks"""
        serializer = BulkTaskActionSerializer(data=request.data)
        
        if serializer.is_valid():
            task_ids = serializer.validated_data['task_ids']
            action = serializer.validated_data['action']
            
            tasks = self.get_queryset().filter(id__in=task_ids)
            
            if action == 'complete':
                updated = tasks.update(status='completed', completed_at=timezone.now())
            elif action == 'reopen':
                updated = tasks.update(status='todo', completed_at=None)
            elif action == 'delete':
                updated = tasks.update(is_deleted=True)
            elif action == 'favorite':
                updated = tasks.update(is_favorite=True)
            elif action == 'unfavorite':
                updated = tasks.update(is_favorite=False)
            else:
                return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'message': f'{action.title()} action performed on {updated} tasks',
                'affected_tasks': updated
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics"""
        now = timezone.now()
        today = now.date()
        week_start = today - timedelta(days=today.weekday())
        
        user_tasks = self.get_queryset()
        
        # Basic counts
        total_tasks = user_tasks.count()
        completed_tasks = user_tasks.filter(status='completed').count()
        pending_tasks = user_tasks.exclude(status='completed').count()
        overdue_tasks = user_tasks.filter(due_date__lt=now).exclude(status='completed').count()
        
        # Time-based counts
        today_tasks = user_tasks.filter(due_date__date=today).count()
        this_week_tasks = user_tasks.filter(due_date__date__gte=week_start).count()
        
        # Completion rate
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Project stats
        user_projects = Project.objects.filter(user=request.user)
        total_projects = user_projects.count()
        active_projects = user_projects.filter(is_archived=False).count()
        
        # Time tracking stats
        time_entries = TimeEntry.objects.filter(task__user=request.user)
        total_time = time_entries.aggregate(total=Sum('duration'))['total']
        total_time_hours = total_time.total_seconds() / 3600 if total_time else 0
        
        week_time = time_entries.filter(start_time__date__gte=week_start).aggregate(
            total=Sum('duration')
        )['total']
        week_time_hours = week_time.total_seconds() / 3600 if week_time else 0
        
        # Priority breakdown
        priority_breakdown = dict(user_tasks.values_list('priority').annotate(Count('priority')))
        
        # Recent activity
        recent_completed = user_tasks.filter(
            completed_at__gte=now - timedelta(days=7)
        ).count()
        
        tasks_created_this_week = user_tasks.filter(
            created_at__gte=week_start
        ).count()
        
        stats = {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'overdue_tasks': overdue_tasks,
            'today_tasks': today_tasks,
            'this_week_tasks': this_week_tasks,
            'completion_rate': round(completion_rate, 1),
            'total_projects': total_projects,
            'active_projects': active_projects,
            'total_time_spent_hours': round(total_time_hours, 1),
            'this_week_time_hours': round(week_time_hours, 1),
            'priority_breakdown': priority_breakdown,
            'recent_completed_tasks': recent_completed,
            'tasks_created_this_week': tasks_created_this_week
        }
        
        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming tasks (due in next 7 days)"""
        now = timezone.now()
        next_week = now + timedelta(days=7)
        
        upcoming_tasks = self.get_queryset().filter(
            due_date__gte=now,
            due_date__lte=next_week
        ).exclude(status='completed').order_by('due_date')
        
        serializer = self.get_serializer(upcoming_tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue tasks"""
        now = timezone.now()
        overdue_tasks = self.get_queryset().filter(
            due_date__lt=now
        ).exclude(status='completed').order_by('due_date')
        
        serializer = self.get_serializer(overdue_tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recurring(self, request):
        """Get recurring tasks"""
        recurring_tasks = self.get_queryset().exclude(recurrence='none')
        serializer = RecurringTaskSerializer(recurring_tasks, many=True)
        return Response(serializer.data)


class SubtaskViewSet(viewsets.ModelViewSet):
    """Subtask management"""
    serializer_class = SubtaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        task_id = self.kwargs.get('task_pk')
        return Subtask.objects.filter(task_id=task_id, task__user=self.request.user)
    
    def perform_create(self, serializer):
        task_id = self.kwargs.get('task_pk')
        task = Task.objects.get(id=task_id, user=self.request.user)
        serializer.save(task=task)
    
    @action(detail=True, methods=['post'])
    def toggle_complete(self, request, task_pk=None, pk=None):
        """Toggle subtask completion"""
        subtask = self.get_object()
        subtask.is_completed = not subtask.is_completed
        subtask.save()
        
        return Response({
            'message': 'Subtask updated',
            'is_completed': subtask.is_completed
        })


class TaskAttachmentViewSet(viewsets.ModelViewSet):
    """Task attachment management"""
    serializer_class = TaskAttachmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        task_id = self.kwargs.get('task_pk')
        return TaskAttachment.objects.filter(task_id=task_id, task__user=self.request.user)
    
    def perform_create(self, serializer):
        task_id = self.kwargs.get('task_pk')
        task = Task.objects.get(id=task_id, user=self.request.user)
        serializer.save(task=task, uploaded_by=self.request.user)


class TaskCommentViewSet(viewsets.ModelViewSet):
    """Task comment management"""
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        task_id = self.kwargs.get('task_pk')
        return TaskComment.objects.filter(task_id=task_id, task__user=self.request.user)
    
    def perform_create(self, serializer):
        task_id = self.kwargs.get('task_pk')
        task = Task.objects.get(id=task_id, user=self.request.user)
        serializer.save(task=task, user=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(is_edited=True)


class TimeEntryViewSet(viewsets.ModelViewSet):
    """Time tracking management"""
    serializer_class = TimeEntrySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        task_id = self.kwargs.get('task_pk')
        return TimeEntry.objects.filter(task_id=task_id, task__user=self.request.user)
    
    def perform_create(self, serializer):
        task_id = self.kwargs.get('task_pk')
        task = Task.objects.get(id=task_id, user=self.request.user)
        serializer.save(task=task, user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def start_timer(self, request, task_pk=None):
        """Start time tracking for task"""
        task = Task.objects.get(id=task_pk, user=request.user)
        
        # Check if there's already an active timer
        active_timer = TimeEntry.objects.filter(
            task=task, user=request.user, end_time__isnull=True
        ).first()
        
        if active_timer:
            return Response({
                'error': 'Timer already running for this task',
                'timer_id': active_timer.id
            }, status=status.HTTP_400_BAD_REQUEST)
        
        timer = TimeEntry.objects.create(
            task=task,
            user=request.user,
            start_time=timezone.now()
        )
        
        return Response({
            'message': 'Timer started',
            'timer_id': timer.id,
            'start_time': timer.start_time
        })
    
    @action(detail=True, methods=['post'])
    def stop_timer(self, request, task_pk=None, pk=None):
        """Stop time tracking"""
        timer = self.get_object()
        
        if timer.end_time:
            return Response({
                'error': 'Timer already stopped'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        timer.end_time = timezone.now()
        timer.save()
        
        return Response({
            'message': 'Timer stopped',
            'duration_hours': timer.duration.total_seconds() / 3600 if timer.duration else 0
        })


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """Notification management"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        
        return Response({'message': 'Notification marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        
        return Response({
            'message': f'{updated} notifications marked as read'
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})
