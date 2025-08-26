# authentication/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    User, EmailVerificationToken, PasswordResetToken, RefreshToken,
    LoginAttempt, UserSession
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom User admin"""
    
    list_display = (
        'email', 'username', 'first_name', 'last_name',
        'is_verified', 'is_active', 'is_staff', 'date_joined'
    )
    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 'is_verified',
        'date_joined', 'last_login'
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'username', 'phone_number', 'bio')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified',
                      'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Settings', {'fields': ('timezone', 'profile_picture')}),
        ('Notifications', {
            'fields': ('email_notifications', 'push_notifications'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile')


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """Email Verification Token admin"""
    
    list_display = ('user', 'token_short', 'created_at', 'expires_at', 'is_used', 'is_expired')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('created_at', 'expires_at', 'is_expired')
    ordering = ('-created_at',)
    
    def token_short(self, obj):
        return f"{obj.token[:10]}..."
    token_short.short_description = 'Token'
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expired'


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Password Reset Token admin"""
    
    list_display = (
        'user', 'token_short', 'created_at', 'expires_at',
        'is_used', 'is_expired', 'ip_address'
    )
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'token', 'ip_address')
    readonly_fields = ('created_at', 'expires_at', 'is_expired')
    ordering = ('-created_at',)
    
    def token_short(self, obj):
        return f"{obj.token[:10]}..."
    token_short.short_description = 'Token'
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expired'


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    """Refresh Token admin"""
    
    list_display = (
        'user', 'token_short', 'created_at', 'expires_at',
        'is_revoked', 'is_expired', 'device_info'
    )
    list_filter = ('is_revoked', 'created_at', 'expires_at')
    search_fields = ('user__email', 'token', 'device_info', 'ip_address')
    readonly_fields = ('created_at', 'expires_at', 'is_expired')
    ordering = ('-created_at',)
    
    def token_short(self, obj):
        return f"{obj.token[:15]}..."
    token_short.short_description = 'Token'
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expired'


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """Login Attempt admin"""
    
    list_display = (
        'email', 'ip_address', 'success', 'attempted_at',
        'failure_reason', 'user_agent_short'
    )
    list_filter = ('success', 'attempted_at')
    search_fields = ('email', 'ip_address', 'failure_reason')
    readonly_fields = ('attempted_at',)
    ordering = ('-attempted_at',)
    
    def user_agent_short(self, obj):
        return obj.user_agent[:50] + "..." if len(obj.user_agent) > 50 else obj.user_agent
    user_agent_short.short_description = 'User Agent'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('email', 'ip_address', 'success', 'failure_reason', 'user_agent')
        return self.readonly_fields


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """User Session admin"""
    
    list_display = (
        'user', 'session_key_short', 'ip_address', 'device_info',
        'created_at', 'last_activity', 'is_active'
    )
    list_filter = ('is_active', 'created_at', 'last_activity')
    search_fields = ('user__email', 'ip_address', 'device_info', 'session_key')
    readonly_fields = ('created_at', 'last_activity')
    ordering = ('-last_activity',)
    
    def session_key_short(self, obj):
        return f"{obj.session_key[:15]}..."
    session_key_short.short_description = 'Session Key'
