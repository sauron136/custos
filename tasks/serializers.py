from rest_framework import serializers
from django.utils import timezone
from accounts.models import UserProfile
from .models import (
    Project, ProjectCollaborator, Category, Tag, Task, 
    Subtask, TaskAttachment, TaskComment, TimeEntry, TaskHistory, Notification
)
from authentication.models import User



class CategorySerializer(serializers.ModelSerializer):
    task_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'color', 'icon', 'task_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'task_count']
    
    def get_task_count(self, obj):
        return obj.task_set.filter(is_deleted=False).count()
    
    def validate_name(self, value):
        user = self.context['request'].user
        if Category.objects.filter(user=user, name__iexact=value).exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise serializers.ValidationError("Category with this name already exists.")
        return value


class TagSerializer(serializers.ModelSerializer):
    task_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'task_count', 'created_at']
        read_only_fields = ['id', 'created_at', 'task_count']
    
    def get_task_count(self, obj):
        return obj.task_set.filter(is_deleted=False).count()
    
    def validate_name(self, value):
        user = self.context['request'].user
        if Tag.objects.filter(user=user, name__iexact=value).exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise serializers.ValidationError("Tag with this name already exists.")
        return value


class ProjectCollaboratorSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    invited_by_username = serializers.CharField(source='invited_by.username', read_only=True)
    
    class Meta:
        model = ProjectCollaborator
        fields = [
            'id', 'user', 'username', 'email', 'full_name', 'role', 
            'invited_by', 'invited_by_username', 'invited_at', 'accepted_at', 'is_active'
        ]
        read_only_fields = ['id', 'invited_at', 'accepted_at']


class ProjectSerializer(serializers.ModelSerializer):
    task_count = serializers.ReadOnlyField()
    completed_task_count = serializers.ReadOnlyField()
    completion_percentage = serializers.ReadOnlyField()
    collaborators_detail = ProjectCollaboratorSerializer(
        source='projectcollaborator_set', many=True, read_only=True
    )
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'color', 'is_favorite', 'is_archived',
            'is_shared', 'task_count', 'completed_task_count', 'completion_percentage',
            'collaborators_detail', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        user = self.context['request'].user
        if Project.objects.filter(user=user, name__iexact=value).exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise serializers.ValidationError("Project with this name already exists.")
        return value


class SubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = ['id', 'title', 'is_completed', 'order', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TaskAttachmentSerializer(serializers.ModelSerializer):
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskAttachment
        fields = [
            'id', 'file', 'original_filename', 'file_size', 'file_size_mb',
            'mime_type', 'uploaded_at', 'uploaded_by'
        ]
        read_only_fields = ['id', 'original_filename', 'file_size', 'uploaded_at', 'uploaded_by']
    
    def get_file_size_mb(self, obj):
        return round(obj.file_size / (1024 * 1024), 2)


class TaskCommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='user.username', read_only=True)
    author_full_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = TaskComment
        fields = [
            'id', 'content', 'author_username', 'author_full_name',
            'created_at', 'updated_at', 'is_edited'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_edited']


class TimeEntrySerializer(serializers.ModelSerializer):
    duration_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = TimeEntry
        fields = [
            'id', 'start_time', 'end_time', 'duration', 'duration_hours',
            'description', 'created_at'
        ]
        read_only_fields = ['id', 'duration', 'created_at']
    
    def get_duration_hours(self, obj):
        if obj.duration:
            return round(obj.duration.total_seconds() / 3600, 2)
        return None
    
    def validate(self, data):
        if data.get('end_time') and data.get('start_time'):
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError("End time must be after start time.")
        return data


class TaskSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    tags_detail = TagSerializer(source='tags', many=True, read_only=True)
    subtasks = SubtaskSerializer(many=True, read_only=True)
    attachments = TaskAttachmentSerializer(many=True, read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    time_entries = TimeEntrySerializer(many=True, read_only=True)
    
    # Computed fields
    is_overdue = serializers.ReadOnlyField()
    days_until_due = serializers.ReadOnlyField()
    subtask_progress = serializers.SerializerMethodField()
    total_time_spent_hours = serializers.SerializerMethodField()
    
    # Assigned user details
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    assigned_to_full_name = serializers.CharField(source='assigned_to.full_name', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority', 'due_date',
            'reminder_date', 'start_date', 'completed_at', 'recurrence',
            'recurrence_end_date', 'time_spent', 'is_favorite', 'is_overdue',
            'days_until_due', 'ai_priority_score', 'ai_estimated_duration',
            'project', 'project_name', 'category', 'category_name', 'category_color',
            'tags', 'tags_detail', 'assigned_to', 'assigned_to_username', 'assigned_to_full_name',
            'subtasks', 'subtask_progress', 'attachments', 'comments', 'time_entries',
            'total_time_spent_hours', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'completed_at', 'is_overdue', 'days_until_due', 
            'created_at', 'updated_at'
        ]
    
    def get_subtask_progress(self, obj):
        total_subtasks = obj.subtasks.count()
        if total_subtasks == 0:
            return None
        completed_subtasks = obj.subtasks.filter(is_completed=True).count()
        return {
            'total': total_subtasks,
            'completed': completed_subtasks,
            'percentage': round((completed_subtasks / total_subtasks) * 100)
        }
    
    def get_total_time_spent_hours(self, obj):
        total_seconds = sum([entry.duration.total_seconds() for entry in obj.time_entries.all() if entry.duration])
        return round(total_seconds / 3600, 2) if total_seconds > 0 else 0
    
    def validate(self, data):
        # Validate due date
        if data.get('due_date') and data.get('start_date'):
            if data['due_date'] <= data['start_date']:
                raise serializers.ValidationError("Due date must be after start date.")
        
        # Validate reminder date
        if data.get('reminder_date') and data.get('due_date'):
            if data['reminder_date'] > data['due_date']:
                raise serializers.ValidationError("Reminder date cannot be after due date.")
        
        # Validate recurrence end date
        if data.get('recurrence') != 'none' and data.get('recurrence_end_date'):
            if data.get('due_date'):
                due_date = data['due_date'].date() if hasattr(data['due_date'], 'date') else data['due_date']
                if data['recurrence_end_date'] <= due_date:
                    raise serializers.ValidationError("Recurrence end date must be after due date.")
        
        return data
    
    def update(self, instance, validated_data):
        # Track status changes
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        # Handle task completion
        if old_status != 'completed' and new_status == 'completed':
            validated_data['completed_at'] = timezone.now()
        elif old_status == 'completed' and new_status != 'completed':
            validated_data['completed_at'] = None
        
        return super().update(instance, validated_data)


class TaskCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for task creation"""
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'status', 'priority', 'due_date',
            'reminder_date', 'start_date', 'recurrence', 'recurrence_end_date',
            'project', 'category', 'tags', 'assigned_to'
        ]
    
    def validate(self, data):
        # Same validation as TaskSerializer
        if data.get('due_date') and data.get('start_date'):
            if data['due_date'] <= data['start_date']:
                raise serializers.ValidationError("Due date must be after start date.")
        
        if data.get('reminder_date') and data.get('due_date'):
            if data['reminder_date'] > data['due_date']:
                raise serializers.ValidationError("Reminder date cannot be after due date.")
        
        return data


class TaskListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for task lists"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    tags_detail = TagSerializer(source='tags', many=True, read_only=True)
    subtask_count = serializers.SerializerMethodField()
    completed_subtasks = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'priority', 'due_date', 'is_favorite',
            'is_overdue', 'days_until_due', 'category_name', 'project_name',
            'tags_detail', 'subtask_count', 'completed_subtasks', 'created_at'
        ]
    
    def get_subtask_count(self, obj):
        return obj.subtasks.count()
    
    def get_completed_subtasks(self, obj):
        return obj.subtasks.filter(is_completed=True).count()


class TaskHistorySerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    
    class Meta:
        model = TaskHistory
        fields = [
            'id', 'action', 'changes', 'timestamp', 
            'user_username', 'task_title'
        ]
        read_only_fields = ['id', 'timestamp']


class NotificationSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source='task.title', read_only=True)
    task_id = serializers.UUIDField(source='task.id', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'message', 'is_read', 'is_sent',
            'task_id', 'task_title', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# Bulk operations serializers
class BulkTaskActionSerializer(serializers.Serializer):
    task_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )
    action = serializers.ChoiceField(choices=[
        ('complete', 'Complete'),
        ('reopen', 'Reopen'),
        ('delete', 'Delete'),
        ('archive', 'Archive'),
        ('favorite', 'Add to Favorites'),
        ('unfavorite', 'Remove from Favorites')
    ])
    
    def validate_task_ids(self, value):
        if len(value) > 50:  # Limit bulk operations
            raise serializers.ValidationError("Cannot perform bulk action on more than 50 tasks.")
        return value


class TaskFilterSerializer(serializers.Serializer):
    """Serializer for task filtering parameters"""
    status = serializers.MultipleChoiceField(
        choices=Task.STATUS_CHOICES,
        required=False
    )
    priority = serializers.MultipleChoiceField(
        choices=Task.PRIORITY_CHOICES,
        required=False
    )
    project = serializers.UUIDField(required=False)
    category = serializers.UUIDField(required=False)
    tags = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    assigned_to = serializers.UUIDField(required=False)
    is_favorite = serializers.BooleanField(required=False)
    is_overdue = serializers.BooleanField(required=False)
    due_date_from = serializers.DateTimeField(required=False)
    due_date_to = serializers.DateTimeField(required=False)
    search = serializers.CharField(max_length=255, required=False)
    
    def validate(self, data):
        if data.get('due_date_from') and data.get('due_date_to'):
            if data['due_date_from'] > data['due_date_to']:
                raise serializers.ValidationError("due_date_from cannot be after due_date_to")
        return data


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    pending_tasks = serializers.IntegerField()
    overdue_tasks = serializers.IntegerField()
    today_tasks = serializers.IntegerField()
    this_week_tasks = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    
    # Project stats
    total_projects = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    
    # Time tracking
    total_time_spent_hours = serializers.FloatField()
    this_week_time_hours = serializers.FloatField()
    
    # Priority breakdown
    priority_breakdown = serializers.DictField()
    
    # Recent activity
    recent_completed_tasks = serializers.IntegerField()
    tasks_created_this_week = serializers.IntegerField()


class ProjectInviteSerializer(serializers.Serializer):
    """Serializer for inviting users to projects"""
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=ProjectCollaborator.ROLE_CHOICES)
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            project = self.context.get('project')
            
            # Check if user is already a collaborator
            if ProjectCollaborator.objects.filter(project=project, user=user).exists():
                raise serializers.ValidationError("User is already a collaborator on this project.")
            
            # Check if user is the project owner
            if project.user == user:
                raise serializers.ValidationError("Cannot invite the project owner as a collaborator.")
                
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
        
        return value


class RecurringTaskSerializer(serializers.ModelSerializer):
    """Serializer for managing recurring tasks"""
    next_due_date = serializers.SerializerMethodField()
    instances_created = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'recurrence', 'recurrence_end_date',
            'due_date', 'next_due_date', 'instances_created',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_next_due_date(self, obj):
        # Logic to calculate next due date based on recurrence
        if obj.recurrence == 'none' or not obj.due_date:
            return None
        
        from datetime import timedelta
        
        if obj.recurrence == 'daily':
            return obj.due_date + timedelta(days=1)
        elif obj.recurrence == 'weekly':
            return obj.due_date + timedelta(weeks=1)
        elif obj.recurrence == 'monthly':
            return obj.due_date + timedelta(days=30)  # Approximation
        elif obj.recurrence == 'yearly':
            return obj.due_date + timedelta(days=365)  # Approximation
        
        return None
    
    def get_instances_created(self, obj):
        return Task.objects.filter(parent_recurring_task=obj).count()
