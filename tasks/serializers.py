from rest_framework import serializers
from .models import Project, Context, Tag, Task, TaskTag, TaskNote, Review

class ProjectSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'user', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

class ContextSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Context
        fields = ['id', 'name', 'user', 'icon']
        read_only_fields = ['id']

class TagSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Tag
        fields = ['id', 'name', 'user', 'color']
        read_only_fields = ['id']

class TaskSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all(), allow_null=True)
    context = serializers.PrimaryKeyRelatedField(queryset=Context.objects.all(), allow_null=True)
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all(), required=False)
    is_overdue = serializers.BooleanField(read_only=True)
    subtasks = serializers.PrimaryKeyRelatedField(many=True, read_only=True, source='task_set')

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'user', 'project', 'context', 'tags',
            'status', 'priority', 'created_at', 'updated_at', 'due_date',
            'completed_at', 'estimated_minutes', 'is_recurring', 'recurring_pattern',
            'energy_level', 'parent', 'subtasks', 'is_overdue'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at', 'is_overdue']

class TaskTagSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all())
    tag = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all())

    class Meta:
        model = TaskTag
        fields = ['id', 'task', 'tag']
        read_only_fields = ['id']

class TaskNoteSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all())

    class Meta:
        model = TaskNote
        fields = ['id', 'task', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'review_type', 'date', 'notes', 'task_completed', 'task_created']
        read_only_fields = ['id']

