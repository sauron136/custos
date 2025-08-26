# accounts/views.py
from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
import logging

from .models import (
    UserProfile, UserAvatar, UserDocument, UserNotificationSettings,
    UserPreferences, UserActivityLog, UserSubscription, TeamInvitation
)
from .serializers import (
    UserProfileSerializer, UserAvatarSerializer, UserDocumentSerializer,
    UserNotificationSettingsSerializer, UserPreferencesSerializer,
    UserActivityLogSerializer, UserSubscriptionSerializer,
    TeamInvitationSerializer, ComprehensiveUserSerializer,
    UpdateUserSerializer
)
from authentication.utils import get_client_ip, create_user_activity_log

User = get_user_model()
logger = logging.getLogger(__name__)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        if created:
            logger.info(f"Created new profile for user: {self.request.user.email}")
        return profile
    
    def perform_update(self, serializer):
        serializer.save()
        create_user_activity_log(
            user=self.request.user,
            action='profile_update',
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details={'updated_fields': list(serializer.validated_data.keys())}
        )


class UserAvatarView(generics.RetrieveUpdateDestroyAPIView):
    """Manage user avatar"""
    serializer_class = UserAvatarSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_object(self):
        avatar, created = UserAvatar.objects.get_or_create(user=self.request.user)
        return avatar
    
    def perform_update(self, serializer):
        # Deactivate old avatar if uploading new one
        if 'image' in serializer.validated_data:
            UserAvatar.objects.filter(user=self.request.user).update(is_active=False)
        
        serializer.save(user=self.request.user, is_active=True)
        create_user_activity_log(
            user=self.request.user,
            action='avatar_upload',
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    def perform_destroy(self, instance):
        create_user_activity_log(
            user=self.request.user,
            action='avatar_delete',
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        instance.delete()


class UserDocumentListView(generics.ListCreateAPIView):
    """List and create user documents"""
    serializer_class = UserDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['document_type', 'is_private']
    search_fields = ['title', 'description']
    ordering_fields = ['uploaded_at', 'title']
    ordering = ['-uploaded_at']
    
    def get_queryset(self):
        return UserDocument.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        create_user_activity_log(
            user=self.request.user,
            action='document_upload',
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details={'document_title': serializer.validated_data['title']}
        )


class UserDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific document"""
    serializer_class = UserDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        return UserDocument.objects.filter(user=self.request.user)


class NotificationSettingsView(generics.RetrieveUpdateAPIView):
    """Get and update notification settings"""
    serializer_class = UserNotificationSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        settings, created = UserNotificationSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings
    
    def perform_update(self, serializer):
        serializer.save()
        create_user_activity_log(
            user=self.request.user,
            action='settings_change',
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details={'settings_type': 'notifications'}
        )


class UserPreferencesView(generics.RetrieveUpdateAPIView):
    """Get and update user preferences"""
    serializer_class = UserPreferencesSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        preferences, created = UserPreferences.objects.get_or_create(
            user=self.request.user
        )
        return preferences
    
    def perform_update(self, serializer):
        serializer.save()
        create_user_activity_log(
            user=self.request.user,
            action='settings_change',
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details={'settings_type': 'preferences'}
        )


class UserActivityLogView(generics.ListAPIView):
    """List user activity logs"""
    serializer_class = UserActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['action']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        return UserActivityLog.objects.filter(user=self.request.user)


class UserSubscriptionView(generics.RetrieveUpdateAPIView):
    """Get and update user subscription"""
    serializer_class = UserSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        subscription, created = UserSubscription.objects.get_or_create(
            user=self.request.user
        )
        return subscription


class ComprehensiveUserView(generics.RetrieveAPIView):
    """Get comprehensive user data including all related models"""
    serializer_class = ComprehensiveUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UpdateBasicUserInfoView(generics.UpdateAPIView):
    """Update basic user information"""
    serializer_class = UpdateUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def perform_update(self, serializer):
        serializer.save()
        create_user_activity_log(
            user=self.request.user,
            action='profile_update',
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            details={'updated_fields': list(serializer.validated_data.keys())}
        )


class TeamInvitationListView(generics.ListCreateAPIView):
    """List and create team invitations"""
    serializer_class = TeamInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'role']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Return invitations sent by the current user
        return TeamInvitation.objects.filter(inviter=self.request.user)
    
    def perform_create(self, serializer):
        import secrets
        from datetime import timedelta
        
        # Generate invitation token
        token = secrets.token_urlsafe(50)
        
        # Set expiration date (7 days from now)
        expires_at = timezone.now() + timedelta(days=7)
        
        serializer.save(
            inviter=self.request.user,
            token=token,
            expires_at=expires_at
        )
        
        # Send invitation email (implement according to your email system)
        self.send_invitation_email(serializer.instance)
    
    def send_invitation_email(self, invitation):
        """Send invitation email to invitee"""
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        try:
            subject = f'Team Invitation from {invitation.inviter.full_name}'
            message = render_to_string('emails/team_invitation.html', {
                'invitation': invitation,
                'inviter': invitation.inviter,
                'accept_url': f"{settings.FRONTEND_URL}/invitations/{invitation.token}/accept",
                'decline_url': f"{settings.FRONTEND_URL}/invitations/{invitation.token}/decline",
            })
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [invitation.invitee_email],
                html_message=message,
                fail_silently=False
            )
            
            logger.info(f"Invitation email sent to {invitation.invitee_email}")
            
        except Exception as e:
            logger.error(f"Failed to send invitation email: {str(e)}")


class ReceivedInvitationsView(generics.ListAPIView):
    """List invitations received by the current user"""
    serializer_class = TeamInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'role']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return TeamInvitation.objects.filter(
            Q(invitee_email=self.request.user.email) |
            Q(invitee=self.request.user)
        )


class TeamInvitationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Manage specific team invitation"""
    serializer_class = TeamInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only manage invitations they sent
        return TeamInvitation.objects.filter(inviter=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def accept_invitation(request, token):
    """Accept a team invitation"""
    try:
        invitation = TeamInvitation.objects.get(token=token)
        
        # Check if user is the intended recipient
        if (invitation.invitee_email != request.user.email and 
            invitation.invitee != request.user):
            return Response({
                'error': 'You are not authorized to accept this invitation.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if invitation.is_expired:
            return Response({
                'error': 'This invitation has expired.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if invitation.status != 'pending':
            return Response({
                'error': 'This invitation has already been responded to.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Accept the invitation
        invitation.accept()
        
        # Set invitee if not already set
        if not invitation.invitee:
            invitation.invitee = request.user
            invitation.save()
        
        # Log activity
        create_user_activity_log(
            user=request.user,
            action='team_invitation_accepted',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={'inviter': invitation.inviter.email}
        )
        
        return Response({
            'message': 'Invitation accepted successfully.',
            'invitation': TeamInvitationSerializer(invitation).data
        }, status=status.HTTP_200_OK)
        
    except TeamInvitation.DoesNotExist:
        return Response({
            'error': 'Invalid invitation token.'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def decline_invitation(request, token):
    """Decline a team invitation"""
    try:
        invitation = TeamInvitation.objects.get(token=token)
        
        # Check if user is the intended recipient
        if (invitation.invitee_email != request.user.email and 
            invitation.invitee != request.user):
            return Response({
                'error': 'You are not authorized to decline this invitation.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if invitation.status != 'pending':
            return Response({
                'error': 'This invitation has already been responded to.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Decline the invitation
        invitation.decline()
        
        # Set invitee if not already set
        if not invitation.invitee:
            invitation.invitee = request.user
            invitation.save()
        
        # Log activity
        create_user_activity_log(
            user=request.user,
            action='team_invitation_declined',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            details={'inviter': invitation.inviter.email}
        )
        
        return Response({
            'message': 'Invitation declined successfully.',
            'invitation': TeamInvitationSerializer(invitation).data
        }, status=status.HTTP_200_OK)
        
    except TeamInvitation.DoesNotExist:
        return Response({
            'error': 'Invalid invitation token.'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def deactivate_account(request):
    """Deactivate user account"""
    user = request.user
    
    # Deactivate the account
    user.is_active = False
    user.save()
    
    # Log activity
    create_user_activity_log(
        user=user,
        action='account_deactivation',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        details={'deactivated_at': timezone.now().isoformat()}
    )
    
    logger.info(f"Account deactivated: {user.email}")
    
    return Response({
        'message': 'Account deactivated successfully.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def export_user_data(request):
    """Export user data"""
    from django.http import JsonResponse
    from tasks.models import Task, Project, Context
    import json
    
    user = request.user
    export_format = request.data.get('format', 'json')
    
    # Gather user data
    user_data = {
        'user_info': {
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        },
        'profile': {},
        'preferences': {},
        'notification_settings': {},
        'tasks': [],
        'projects': [],
        'contexts': [],
        'activity_logs': []
    }
    
    # Add profile data
    try:
        profile = user.profile
        user_data['profile'] = UserProfileSerializer(profile).data
    except UserProfile.DoesNotExist:
        pass
    
    # Add preferences
    try:
        preferences = user.preferences
        user_data['preferences'] = UserPreferencesSerializer(preferences).data
    except UserPreferences.DoesNotExist:
        pass
    
    # Add notification settings
    try:
        settings = user.notification_settings
        user_data['notification_settings'] = UserNotificationSettingsSerializer(settings).data
    except UserNotificationSettings.DoesNotExist:
        pass
    
    # Add tasks
    tasks = Task.objects.filter(user=user)
    user_data['tasks'] = [
        {
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'created_at': task.created_at.isoformat(),
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        }
        for task in tasks
    ]
    
    # Add projects
    projects = Project.objects.filter(user=user)
    user_data['projects'] = [
        {
            'name': project.name,
            'description': project.description,
            'color': project.color,
            'is_active': project.is_active,
            'created_at': project.created_at.isoformat(),
        }
        for project in projects
    ]
    
    # Add contexts
    contexts = Context.objects.filter(user=user)
    user_data['contexts'] = [
        {
            'name': context.name,
            'icon': context.icon,
        }
        for context in contexts
    ]
    
    # Add recent activity logs (last 100)
    logs = UserActivityLog.objects.filter(user=user)[:100]
    user_data['activity_logs'] = UserActivityLogSerializer(logs, many=True).data
    
    # Log the export
    create_user_activity_log(
        user=user,
        action='data_export',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        details={'export_format': export_format}
    )
    
    if export_format == 'json':
        return Response(user_data, status=status.HTTP_200_OK)
    else:
        # For other formats, you might want to return a file download
        # This is a simplified JSON response for now
        return Response({
            'message': 'Data export ready',
            'data': user_data
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics for the user"""
    from tasks.models import Task, Project
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    
    user = request.user
    now = timezone.now()
    
    # Task statistics
    tasks = Task.objects.filter(user=user)
    overdue_tasks = [task for task in tasks if task.is_overdue]
    
    # Recent activity (last 30 days)
    thirty_days_ago = now - timedelta(days=30)
    recent_tasks = tasks.filter(created_at__gte=thirty_days_ago)
    completed_recently = tasks.filter(
        completed_at__gte=thirty_days_ago,
        status='done'
    )
    
    # Project statistics
    projects = Project.objects.filter(user=user, is_active=True)
    
    stats = {
        'tasks': {
            'total': tasks.count(),
            'completed': tasks.filter(status='done').count(),
            'pending': tasks.filter(status__in=['inbox', 'next']).count(),
            'overdue': len(overdue_tasks),
            'created_this_month': recent_tasks.count(),
            'completed_this_month': completed_recently.count(),
        },
        'projects': {
            'total': projects.count(),
            'active': projects.count(),
        },
        'productivity': {
            'completion_rate': 0,
            'average_completion_time': 0,
        }
    }
    
    # Calculate completion rate
    total_tasks = stats['tasks']['total']
    if total_tasks > 0:
        stats['productivity']['completion_rate'] = round(
            (stats['tasks']['completed'] / total_tasks) * 100, 1
        )
    
    return Response(stats, status=status.HTTP_200_OK)
