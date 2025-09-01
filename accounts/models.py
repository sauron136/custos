from django.db import models
from django.utils import timezone
from authentication.models import User
import uuid
from datetime import timedelta


class UserProfile(models.Model):
    """Extended user profile for task manager"""
    
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto'),
    ]
    
    DEFAULT_VIEW_CHOICES = [
        ('list', 'List View'),
        ('board', 'Board View'),
        ('calendar', 'Calendar View'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Task Manager Preferences
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    default_view = models.CharField(max_length=10, choices=DEFAULT_VIEW_CHOICES, default='list')
    email_reminders = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    daily_email_summary = models.BooleanField(default=False)
    
    # AI Preferences (for future use)
    ai_prioritization_enabled = models.BooleanField(default=False)
    ai_suggestions_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
