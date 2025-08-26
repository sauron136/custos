# accounts/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    UserProfile, UserAvatar, UserDocument, UserNotificationSettings,
    UserPreferences, UserActivityLog, UserSubscription, TeamInvitation
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """User Profile admin"""
    
    list_display = (
        'user', 'job_title', 'company', 'city', 'country',
        'theme', 'language', 'profile_visibility'
    )
    list_filter = (
        'theme', 'language', 'profile_visibility', 'gender',
        'allow_task_sharing', 'allow_team_invitations'
    )
    search_fields = (
        'user__email', 'user__first_name', 'user__last_name',
        'job_title', 'company', 'city', 'country'
    )
    readonly_fields = ('created_at', 'updated_at', 'full_address')
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Personal Information', {
            'fields': ('date_of_birth', 'gender', 'job_title', 'company', 'department', 'manager')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code', 'full_address'),
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': (
                'theme', 'language', 'date_format', 'time_format',
                'default_task_priority', 'default_task_context'
            )
        }),
        ('Task Settings', {
            'fields': ('show_completed_tasks', 'task_reminder_time'),
            'classes': ('collapse',)
        }),
        ('Privacy', {
            'fields': ('profile_visibility', 'allow_task_sharing', 'allow_team_invitations')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserAvatar)
class UserAvatarAdmin(admin.ModelAdmin):
    """User Avatar admin"""
    
    list_display = ('user', 'image_preview', 'uploaded_at', 'is_active')
    list_filter = ('is_active', 'uploaded_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('uploaded_at', 'image_preview')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = 'Preview'


@admin.register(UserDocument)
class UserDocumentAdmin(admin.ModelAdmin):
    """User Document admin"""
    
    list_display = (
        'user', 'title', 'document_type', 'file_size_formatted',
        'is_private', 'uploaded_at'
    )
    list_filter = ('document_type', 'is_private', 'uploaded_at')
    search_fields = ('user__email', 'title', 'description')
    readonly_fields = ('uploaded_at', 'file_size', 'file_extension')
    
    def file_size_formatted(self, obj):
        size = obj.file_size
        if size == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
    file_size_formatted.short_description = 'File Size'


@admin.register(UserNotificationSettings)
class UserNotificationSettingsAdmin(admin.ModelAdmin):
    """User Notification Settings admin"""
    
    list_display = (
        'user', 'email_task_reminders', 'email_task_assignments',
        'push_task_reminders', 'weekend_notifications'
    )
    list_filter = (
        'email_task_reminders', 'email_task_assignments',
        'push_task_reminders', 'weekend_notifications'
    )
    search_fields = ('user__email',)
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Email Notifications', {
            'fields': (
                'email_task_reminders', 'email_task_assignments',
                'email_project_updates', 'email_team_invitations',
                'email_weekly_summary', 'email_marketing'
            )
        }),
        ('Push Notifications', {
            'fields': (
                'push_task_reminders', 'push_task_assignments',
                'push_project_updates', 'push_team_invitations'
            )
        }),
        ('In-App Notifications', {
            'fields': (
                'app_task_reminders', 'app_task_assignments',
                'app_project_updates', 'app_team_invitations'
            )
        }),
        ('Timing Settings', {
            'fields': ('quiet_hours_start', 'quiet_hours_end', 'weekend_notifications')
        }),
    )


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    """User Preferences admin"""
    
    list_display = (
        'user', 'dashboard_layout', 'default_task_view',
        'tasks_per_page', 'two_factor_enabled'
    )
    list_filter = (
        'dashboard_layout', 'default_task_view', 'two_factor_enabled',
        'login_notifications', 'export_format'
    )
    search_fields = ('user__email',)


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    """User Activity Log admin"""
    
    list_display = (
        'user', 'action', 'description_short', 'ip_address', 'timestamp'
    )
    list_filter = ('action', 'timestamp')
    search_fields = ('user__email', 'action', 'description', 'ip_address')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def description_short(self, obj):
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    """User Subscription admin"""
    
    list_display = (
        'user', 'plan', 'status', 'amount', 'currency',
        'started_at', 'expires_at', 'is_active'
    )
    list_filter = ('plan', 'status', 'billing_cycle', 'auto_renew')
    search_fields = ('user__email', 'stripe_customer_id', 'stripe_subscription_id')
    readonly_fields = ('started_at', 'is_active', 'is_trial', 'days_until_expiry')
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Subscription Details', {
            'fields': ('plan', 'status', 'started_at', 'expires_at', 'trial_ends_at')
        }),
        ('Billing', {
            'fields': ('billing_cycle', 'amount', 'currency', 'auto_renew')
        }),
        ('External IDs', {
            'fields': ('stripe_customer_id', 'stripe_subscription_id'),
            'classes': ('collapse',)
        }),
        ('Limits', {
            'fields': ('tasks_limit', 'projects_limit', 'storage_limit_mb')
        }),
        ('Status', {
            'fields': ('is_active', 'is_trial', 'days_until_expiry'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TeamInvitation)
class TeamInvitationAdmin(admin.ModelAdmin):
    """Team Invitation admin"""
    
    list_display = (
        'inviter', 'invitee_email', 'role', 'status',
        'created_at', 'expires_at', 'is_expired'
    )
    list_filter = ('role', 'status', 'created_at', 'expires_at')
    search_fields = (
        'inviter__email', 'invitee_email', 'invitee__email', 'message'
    )
    readonly_fields = ('created_at', 'responded_at', 'is_expired')
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expired'

