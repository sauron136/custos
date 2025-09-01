from rest_framework import serializers
from django.utils import timezone
from .models import UserProfile
from authentication.models import User


class UserProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'user_email', 'user_username', 'full_name', 'avatar', 'bio', 
            'timezone', 'theme', 'default_view', 'email_reminders', 
            'push_notifications', 'daily_email_summary', 'ai_prioritization_enabled',
            'ai_suggestions_enabled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
