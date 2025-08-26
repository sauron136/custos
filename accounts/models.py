# accounts/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import os

User = get_user_model()


def user_avatar_path(instance, filename):
    """Generate file path for user avatar"""
    ext = filename.split('.')[-1]
    filename = f"avatar_{instance.user.id}.{ext}"
    return os.path.join('avatars', str(instance.user.id), filename)


def user_document_path(instance, filename):
    """Generate file path for user documents"""
    return os.path.join('documents', str(instance.user.id), filename)


class UserProfile(models.Model):
    """Extended user profile information"""
    
    THEME_CHOICES = [
        ('light', 'Light Theme'),
        ('dark', 'Dark Theme'),
        ('auto', 'Auto (System)'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('zh', 'Chinese'),
        ('ja', 'Japanese'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Personal information
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ], blank=True)
    
    # Contact information
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Professional information
    job_title = models.CharField(max_length=200, blank=True)
    company = models.CharField(max_length=200, blank=True)
    department = models.CharField(max_length=100, blank=True)
    manager = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='managed_users'
    )
    
    # Preferences
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='auto')
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    date_format = models.CharField(max_length=20, default='MM/DD/YYYY')
    time_format = models.CharField(max_length=10, choices=[
        ('12h', '12 Hour'),
        ('24h', '24 Hour'),
    ], default='12h')
    
    # Task preferences
    default_task_priority = models.IntegerField(default=2, choices=[
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Urgent'),
    ])
    default_task_context = models.CharField(max_length=100, blank=True)
    show_completed_tasks = models.BooleanField(default=False)
    task_reminder_time = models.IntegerField(default=15)  # minutes before due date
    
    # Privacy settings
    profile_visibility = models.CharField(max_length=10, choices=[
        ('public', 'Public'),
        ('private', 'Private'),
        ('team', 'Team Only'),
    ], default='private')
    
    allow_task_sharing = models.BooleanField(default=True)
    allow_team_invitations = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile for {self.user.email}"
    
    @property
    def full_address(self):
        """Return formatted full address"""
        parts = [self.address, self.city, self.state, self.postal_code, self.country]
        return ', '.join(filter(None, parts))


class UserAvatar(models.Model):
    """User avatar/profile picture management"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='avatar')
    image = models.ImageField(
        upload_to=user_avatar_path,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Avatar for {self.user.email}"
    
    def delete(self, *args, **kwargs):
        """Delete the file when the model instance is deleted"""
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)


class UserDocument(models.Model):
    """User document storage"""
    
    DOCUMENT_TYPES = [
        ('id', 'ID Document'),
        ('resume', 'Resume'),
        ('certificate', 'Certificate'),
        ('contract', 'Contract'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=user_document_path)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='other')
    is_private = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    @property
    def file_size(self):
        """Return file size in bytes"""
        try:
            return self.file.size
        except:
            return 0
    
    @property
    def file_extension(self):
        """Return file extension"""
        return os.path.splitext(self.file.name)[1]
    
    def delete(self, *args, **kwargs):
        """Delete the file when the model instance is deleted"""
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)


class UserNotificationSettings(models.Model):
    """User notification preferences"""
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='notification_settings'
    )
    
    # Email notifications
    email_task_reminders = models.BooleanField(default=True)
    email_task_assignments = models.BooleanField(default=True)
    email_project_updates = models.BooleanField(default=True)
    email_team_invitations = models.BooleanField(default=True)
    email_weekly_summary = models.BooleanField(default=True)
    email_marketing = models.BooleanField(default=False)
    
    # Push notifications (for mobile app)
    push_task_reminders = models.BooleanField(default=True)
    push_task_assignments = models.BooleanField(default=True)
    push_project_updates = models.BooleanField(default=False)
    push_team_invitations = models.BooleanField(default=True)
    
    # In-app notifications
    app_task_reminders = models.BooleanField(default=True)
    app_task_assignments = models.BooleanField(default=True)
    app_project_updates = models.BooleanField(default=True)
    app_team_invitations = models.BooleanField(default=True)
    
    # Notification timing
    quiet_hours_start = models.TimeField(default='22:00')
    quiet_hours_end = models.TimeField(default='07:00')
    weekend_notifications = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification settings for {self.user.email}"


class UserPreferences(models.Model):
    """Additional user preferences and settings"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # Dashboard preferences
    dashboard_widgets = models.JSONField(default=list)  # List of enabled widgets
    dashboard_layout = models.CharField(max_length=20, choices=[
        ('grid', 'Grid Layout'),
        ('list', 'List Layout'),
        ('compact', 'Compact Layout'),
    ], default='grid')
    
    # Task view preferences
    tasks_per_page = models.IntegerField(default=25)
    default_task_view = models.CharField(max_length=20, choices=[
        ('list', 'List View'),
        ('kanban', 'Kanban Board'),
        ('calendar', 'Calendar View'),
        ('timeline', 'Timeline View'),
    ], default='list')
    show_task_descriptions = models.BooleanField(default=True)
    show_task_due_dates = models.BooleanField(default=True)
    show_task_priorities = models.BooleanField(default=True)
    show_task_contexts = models.BooleanField(default=True)
    
    # Productivity settings
    work_hours_start = models.TimeField(default='09:00')
    work_hours_end = models.TimeField(default='17:00')
    break_duration = models.IntegerField(default=15)  # minutes
    focus_session_duration = models.IntegerField(default=25)  # Pomodoro timer
    
    # Data export preferences
    export_format = models.CharField(max_length=10, choices=[
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
        ('xlsx', 'Excel'),
    ], default='json')
    
    # Security preferences
    two_factor_enabled = models.BooleanField(default=False)
    login_notifications = models.BooleanField(default=True)
    session_timeout = models.IntegerField(default=30)  # minutes
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferences for {self.user.email}"


class UserActivityLog(models.Model):
    """Log of user activities for audit trail"""
    
    ACTION_CHOICES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('password_change', 'Password Changed'),
        ('profile_update', 'Profile Updated'),
        ('email_verification', 'Email Verified'),
        ('password_reset', 'Password Reset'),
        ('avatar_upload', 'Avatar Uploaded'),
        ('document_upload', 'Document Uploaded'),
        ('settings_change', 'Settings Changed'),
        ('account_deactivation', 'Account Deactivated'),
        ('account_reactivation', 'Account Reactivated'),
        ('data_export', 'Data Exported'),
        ('privacy_settings_change', 'Privacy Settings Changed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict)  # Additional context data
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_action_display()} - {self.timestamp}"


class UserSubscription(models.Model):
    """User subscription and billing information"""
    
    PLAN_CHOICES = [
        ('free', 'Free Plan'),
        ('basic', 'Basic Plan'),
        ('premium', 'Premium Plan'),
        ('enterprise', 'Enterprise Plan'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('trial', 'Trial'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Subscription details
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=False)
    
    # Billing
    billing_cycle = models.CharField(max_length=10, choices=[
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ], default='monthly')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    
    # External service IDs (for payment processors)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    
    # Usage tracking
    tasks_limit = models.IntegerField(default=50)  # -1 for unlimited
    projects_limit = models.IntegerField(default=5)  # -1 for unlimited
    storage_limit_mb = models.IntegerField(default=100)  # MB, -1 for unlimited
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.get_plan_display()}"
    
    @property
    def is_active(self):
        """Check if subscription is currently active"""
        if self.status != 'active':
            return False
        
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        
        return True
    
    @property
    def is_trial(self):
        """Check if user is in trial period"""
        if self.trial_ends_at and timezone.now() < self.trial_ends_at:
            return True
        return False
    
    @property
    def days_until_expiry(self):
        """Get days until subscription expires"""
        if not self.expires_at:
            return None
        
        delta = self.expires_at - timezone.now()
        return delta.days if delta.days > 0 else 0


class TeamInvitation(models.Model):
    """Team invitation system"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('viewer', 'Viewer'),
    ]
    
    inviter = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_invitations'
    )
    invitee_email = models.EmailField()
    invitee = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_invitations',
        null=True, 
        blank=True
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Invitation details
    message = models.TextField(blank=True)
    token = models.CharField(max_length=100, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('inviter', 'invitee_email')
    
    def __str__(self):
        return f"Invitation from {self.inviter.email} to {self.invitee_email}"
    
    @property
    def is_expired(self):
        """Check if invitation has expired"""
        return timezone.now() > self.expires_at
    
    def accept(self):
        """Accept the invitation"""
        if self.is_expired:
            raise ValueError("Invitation has expired")
        
        self.status = 'accepted'
        self.responded_at = timezone.now()
        self.save()
    
    def decline(self):
        """Decline the invitation"""
        self.status = 'declined'
        self.responded_at = timezone.now()
        self.save()
