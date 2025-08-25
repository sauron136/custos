# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    UserProfile, UserAvatar, UserDocument, UserNotificationSettings,
    UserPreferences, UserActivityLog, UserSubscription, TeamInvitation
)

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    
    full_address = serializers.CharField(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = (
            'date_of_birth', 'gender', 'address', 'city', 'state',
            'country', 'postal_code', 'full_address', 'job_title',
            'company', 'department', 'manager', 'theme', 'language',
            'date_format', 'time_format', 'default_task_priority',
            'default_task_context', 'show_completed_tasks',
            'task_reminder_time', 'profile_visibility',
            'allow_task_sharing', 'allow_team_invitations'
        )
        read_only_fields = ('created_at', 'updated_at')


class UserAvatarSerializer(serializers.ModelSerializer):
    """Serializer for user avatar"""
    
    image_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    
    class Meta:
        model = UserAvatar
        fields = ('id', 'image', 'image_url', 'file_size', 'uploaded_at', 'is_active')
        read_only_fields = ('uploaded_at',)
    
    def get_image_url(self, obj):
        """Get full URL for avatar image"""
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None
    
    def get_file_size(self, obj):
        """Get file size in bytes"""
        try:
            return obj.image.size
        except:
            return 0
    
    def validate_image(self, value):
        """Validate image file"""
        # Check file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError("Image file too large. Maximum size is 5MB.")
        
        # Check image dimensions (optional)
        from PIL import Image
        try:
            img = Image.open(value)
            width, height = img.size
            
            # Maximum dimensions
            max_width, max_height = 2000, 2000
            if width > max_width or height > max_height:
                raise serializers.ValidationError(
                    f"Image dimensions too large. Maximum size is {max_width}x{max_height} pixels."
                )
        except Exception:
            raise serializers.ValidationError("Invalid image file.")
        
        return value


class UserDocumentSerializer(serializers.ModelSerializer):
    """Serializer for user documents"""
    
    file_url = serializers.SerializerMethodField()
    file_size_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = UserDocument
        fields = (
            'id', 'title', 'description', 'file', 'file_url',
            'document_type', 'file_size', 'file_size_formatted',
            'file_extension', 'is_private', 'uploaded_at'
        )
        read_only_fields = ('file_size', 'file_extension', 'uploaded_at')
    
    def get_file_url(self, obj):
        """Get full URL for document file"""
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None
    
    def get_file_size_formatted(self, obj):
        """Get formatted file size"""
        size = obj.file_size
        if size == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
    
    def validate_file(self, value):
        """Validate uploaded file"""
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError("File too large. Maximum size is 10MB.")
        
        # Check file extension
        allowed_extensions = [
            'pdf', 'doc', 'docx', 'txt', 'rtf',
            'jpg', 'jpeg', 'png', 'gif', 'bmp',
            'xls', 'xlsx', 'csv', 'ppt', 'pptx'
        ]
        
        file_extension = value.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        return value


class UserNotificationSettingsSerializer(serializers.ModelSerializer):
    """Serializer for notification settings"""
    
    class Meta:
        model = UserNotificationSettings
        fields = (
            'email_task_reminders', 'email_task_assignments',
            'email_project_updates', 'email_team_invitations',
            'email_weekly_summary', 'email_marketing',
            'push_task_reminders', 'push_task_assignments',
            'push_project_updates', 'push_team_invitations',
            'app_task_reminders', 'app_task_assignments',
            'app_project_updates', 'app_team_invitations',
            'quiet_hours_start', 'quiet_hours_end', 'weekend_notifications'
        )


class UserPreferencesSerializer(serializers.ModelSerializer):
    """Serializer for user preferences"""
    
    class Meta:
        model = UserPreferences
        fields = (
            'dashboard_widgets', 'dashboard_layout', 'tasks_per_page',
            'default_task_view', 'show_task_descriptions', 'show_task_due_dates',
            'show_task_priorities', 'show_task_contexts', 'work_hours_start',
            'work_hours_end', 'break_duration', 'focus_session_duration',
            'export_format', 'two_factor_enabled', 'login_notifications',
            'session_timeout'
        )


class UserActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for user activity logs"""
    
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = UserActivityLog
        fields = (
            'id', 'action', 'action_display', 'description',
            'ip_address', 'user_agent', 'details', 'timestamp'
        )
        read_only_fields = ('timestamp',)


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for user subscription"""
    
    plan_display = serializers.CharField(source='get_plan_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_trial = serializers.BooleanField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = (
            'plan', 'plan_display', 'status', 'status_display',
            'started_at', 'expires_at', 'trial_ends_at', 'auto_renew',
            'billing_cycle', 'amount', 'currency', 'tasks_limit',
            'projects_limit', 'storage_limit_mb', 'is_active',
            'is_trial', 'days_until_expiry'
        )
        read_only_fields = (
            'started_at', 'stripe_customer_id', 'stripe_subscription_id'
        )


class TeamInvitationSerializer(serializers.ModelSerializer):
    """Serializer for team invitations"""
    
    inviter_name = serializers.CharField(source='inviter.full_name', read_only=True)
    inviter_email = serializers.CharField(source='inviter.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = TeamInvitation
        fields = (
            'id', 'inviter', 'inviter_name', 'inviter_email',
            'invitee_email', 'role', 'role_display', 'status',
            'status_display', 'message', 'created_at', 'expires_at',
            'responded_at', 'is_expired'
        )
        read_only_fields = (
            'inviter', 'token', 'created_at', 'responded_at'
        )
    
    def validate_invitee_email(self, value):
        """Validate invitee email"""
        # Check if user is trying to invite themselves
        request = self.context.get('request')
        if request and request.user.email == value:
            raise serializers.ValidationError("You cannot invite yourself.")
        
        # Check if invitation already exists
        if self.instance is None:  # Creating new invitation
            existing_invitation = TeamInvitation.objects.filter(
                inviter=request.user,
                invitee_email=value,
                status='pending'
            ).exists()
            
            if existing_invitation:
                raise serializers.ValidationError(
                    "An active invitation already exists for this email."
                )
        
        return value.lower()


class ComprehensiveUserSerializer(serializers.ModelSerializer):
    """Comprehensive user serializer with all related data"""
    
    profile = UserProfileSerializer(read_only=True)
    avatar = UserAvatarSerializer(read_only=True)
    notification_settings = UserNotificationSettingsSerializer(read_only=True)
    preferences = UserPreferencesSerializer(read_only=True)
    subscription = UserSubscriptionSerializer(read_only=True)
    
    # Statistics
    total_tasks = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()
    active_projects = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'phone_number', 'bio', 'timezone',
            'is_verified', 'date_joined', 'last_login',
            'profile', 'avatar', 'notification_settings',
            'preferences', 'subscription', 'total_tasks',
            'completed_tasks', 'active_projects'
        )
        read_only_fields = (
            'id', 'email', 'is_verified', 'date_joined', 'last_login'
        )
    
    def get_total_tasks(self, obj):
        """Get total number of tasks for the user"""
        from tasks.models import Task
        return Task.objects.filter(user=obj).count()
    
    def get_completed_tasks(self, obj):
        """Get number of completed tasks for the user"""
        from tasks.models import Task
        return Task.objects.filter(user=obj, status='done').count()
    
    def get_active_projects(self, obj):
        """Get number of active projects for the user"""
        from tasks.models import Project
        return Project.objects.filter(user=obj, is_active=True).count()


class UpdateUserSerializer(serializers.ModelSerializer):
    """Serializer for updating basic user information"""
    
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'phone_number', 'bio', 'timezone'
        )
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        import re
        if value and not re.match(r'^\+?[\d\s\-\(\)]+$', value):
            raise serializers.ValidationError("Invalid phone number format.")
        return value
