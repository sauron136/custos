from django.db import models
from django.conf import settings
from django.utils import timezone


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    color = models.CharField(max_length=7, default='#3498db')  # Hex color
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class Context(models.Model):
    """Contexts like @home, @calls, @errands for GTD-style organization"""
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    icon = models.CharField(max_length=50, blank=True)  # Font awesome or emoji
    
    def __str__(self):
        return f"@{self.name}"


class Task(models.Model):
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'), 
        (3, 'High'),
        (4, 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('inbox', 'Inbox'),
        ('next', 'Next Actions'),
        ('waiting', 'Waiting For'),
        ('someday', 'Someday/Maybe'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ]
    
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    context = models.ForeignKey(Context, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inbox')
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional fields
    estimated_minutes = models.PositiveIntegerField(null=True, blank=True)
    is_recurring = models.BooleanField(default=False)
    recurring_pattern = models.CharField(max_length=100, blank=True)  # "daily", "weekly", etc.
    energy_level = models.CharField(max_length=20, choices=[
        ('low', 'Low Energy'),
        ('medium', 'Medium Energy'),
        ('high', 'High Energy'),
    ], default='medium')
    
    # Parent task for subtasks
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', 'due_date', 'created_at']
    
    def __str__(self):
        return self.title
    
    def mark_complete(self):
        self.status = 'done'
        self.completed_at = timezone.now()
        self.save()
    
    @property
    def is_overdue(self):
        if self.due_date and self.status not in ['done', 'cancelled']:
            return timezone.now() > self.due_date
        return False
    
    @property
    def subtasks(self):
        return self.task_set.all()


class Tag(models.Model):
    """Flexible tagging system"""
    name = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    color = models.CharField(max_length=7, default='#95a5a6')
    
    def __str__(self):
        return f"#{self.name}"


class TaskTag(models.Model):
    """Many-to-many relationship between tasks and tags"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('task', 'tag')


class TaskNote(models.Model):
    """Notes/comments on tasks for tracking progress"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']


class Review(models.Model):
    """Weekly/periodic reviews for GTD methodology"""
    REVIEW_TYPES = [
        ('daily', 'Daily Review'),
        ('weekly', 'Weekly Review'),
        ('monthly', 'Monthly Review'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPES)
    date = models.DateField()
    notes = models.TextField(blank=True)
    tasks_completed = models.PositiveIntegerField(default=0)
    tasks_created = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('user', 'review_type', 'date')
