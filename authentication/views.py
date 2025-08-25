# authentication/views.py
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
import secrets
import logging

from .models import (
    EmailVerificationToken, PasswordResetToken, RefreshToken as CustomRefreshToken,
    LoginAttempt, UserSession
)
from .serializers import (
    CustomTokenObtainPairSerializer, UserRegistrationSerializer,
    UserSerializer, EmailVerificationSerializer, ResendVerificationSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    ChangePasswordSerializer
)
from .utils import get_client_ip, get_device_info

User = get_user_model()
logger = logging.getLogger(__name__)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view with additional security features"""
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        email = request.data.get('email', '')
        
        # Track login attempt
        try:
            response = super().post(request, *args, **kwargs)
            
            # Success - log successful login
            LoginAttempt.objects.create(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )
            
            # Create user session
            if response.status_code == 200:
                try:
                    user = User.objects.get(email__iexact=email)
                    UserSession.objects.create(
                        user=user,
                        session_key=secrets.token_hex(20),
                        ip_address=ip_address,
                        user_agent=user_agent,
                        device_info=get_device_info(user_agent)
                    )
                except User.DoesNotExist:
                    pass
            
            return response
            
        except Exception as e:
            # Failed login - log attempt with failure reason
            failure_reason = str(e)
            if 'Invalid email or password' in failure_reason:
                failure_reason = 'Invalid credentials'
            elif 'Email not verified' in failure_reason:
                failure_reason = 'Email not verified'
            elif 'User account is disabled' in failure_reason:
                failure_reason = 'Account disabled'
            
            LoginAttempt.objects.create(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                failure_reason=failure_reason
            )
            
            raise


class RegisterView(generics.CreateAPIView):
    """User registration view"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        # Send verification email
        self.send_verification_email(user, request)
        
        return Response({
            'message': 'Registration successful. Please check your email for verification link.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    def send_verification_email(self, user, request):
        """Send email verification link"""
        try:
            # Generate verification token
            token = secrets.token_urlsafe(50)
            EmailVerificationToken.objects.create(
                user=user,
                token=token
            )
            
            # Prepare email content
            verification_url = request.build_absolute_uri(
                reverse('authentication:verify-email', kwargs={'token': token})
            )
            
            subject = 'Verify your email address'
            message = render_to_string('emails/email_verification.html', {
                'user': user,
                'verification_url': verification_url,
                'site_name': getattr(settings, 'SITE_NAME', 'Task Manager')
            })
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=message,
                fail_silently=False
            )
            
            logger.info(f"Verification email sent to {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def verify_email(request, token):
    """Verify user email with token"""
    try:
        verification_token = EmailVerificationToken.objects.get(token=token)
        
        if not verification_token.is_valid:
            return Response({
                'error': 'Verification link has expired or been used.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark user as verified
        user = verification_token.user
        user.is_verified = True
        user.save()
        
        # Mark token as used
        verification_token.is_used = True
        verification_token.save()
        
        logger.info(f"Email verified for user: {user.email}")
        
        return Response({
            'message': 'Email verified successfully. You can now login to your account.'
        }, status=status.HTTP_200_OK)
        
    except EmailVerificationToken.DoesNotExist:
        return Response({
            'error': 'Invalid verification link.'
        }, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationView(generics.GenericAPIView):
    """Resend email verification"""
    serializer_class = ResendVerificationSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email__iexact=email)
        
        # Invalidate old tokens
        EmailVerificationToken.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Send new verification email
        self.send_verification_email(user, request)
        
        return Response({
            'message': 'Verification email sent successfully.'
        }, status=status.HTTP_200_OK)
    
    def send_verification_email(self, user, request):
        """Send email verification link"""
        token = secrets.token_urlsafe(50)
        EmailVerificationToken.objects.create(
            user=user,
            token=token
        )
        
        verification_url = request.build_absolute_uri(
            reverse('authentication:verify-email', kwargs={'token': token})
        )
        
        subject = 'Verify your email address'
        message = render_to_string('emails/email_verification.html', {
            'user': user,
            'verification_url': verification_url,
            'site_name': getattr(settings, 'SITE_NAME', 'Task Manager')
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
            fail_silently=False
        )


class PasswordResetRequestView(generics.GenericAPIView):
    """Request password reset"""
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email__iexact=email)
            
            # Invalidate old reset tokens
            PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
            
            # Create new reset token
            token = secrets.token_urlsafe(50)
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            PasswordResetToken.objects.create(
                user=user,
                token=token,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Send reset email
            self.send_reset_email(user, token, request)
            
        except User.DoesNotExist:
            # Don't reveal if email exists - always return success
            pass
        
        return Response({
            'message': 'If an account with this email exists, a password reset link has been sent.'
        }, status=status.HTTP_200_OK)
    
    def send_reset_email(self, user, token, request):
        """Send password reset email"""
        reset_url = request.build_absolute_uri(
            reverse('authentication:password-reset-confirm', kwargs={'token': token})
        )
        
        subject = 'Password Reset Request'
        message = render_to_string('emails/password_reset.html', {
            'user': user,
            'reset_url': reset_url,
            'site_name': getattr(settings, 'SITE_NAME', 'Task Manager')
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
            fail_silently=False
        )
        
        logger.info(f"Password reset email sent to {user.email}")


class PasswordResetConfirmView(generics.GenericAPIView):
    """Confirm password reset with token"""
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']
        
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            
            if not reset_token.is_valid:
                return Response({
                    'error': 'Reset token has expired or been used.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Reset password
            user = reset_token.user
            user.set_password(password)
            user.save()
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.save()
            
            # Revoke all refresh tokens for security
            CustomRefreshToken.objects.filter(user=user).update(is_revoked=True)
            
            logger.info(f"Password reset successful for user: {user.email}")
            
            return Response({
                'message': 'Password reset successful. You can now login with your new password.'
            }, status=status.HTTP_200_OK)
            
        except PasswordResetToken.DoesNotExist:
            return Response({
                'error': 'Invalid reset token.'
            }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(generics.GenericAPIView):
    """Change password for authenticated user"""
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Change password
        user = request.user
        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        
        # Revoke all refresh tokens for security
        CustomRefreshToken.objects.filter(user=user).update(is_revoked=True)
        
        logger.info(f"Password changed for user: {user.email}")
        
        return Response({
            'message': 'Password changed successfully. Please login again with your new password.'
        }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class LogoutView(generics.GenericAPIView):
    """Logout user by revoking refresh token"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            
            if refresh_token:
                # Revoke the specific refresh token
                token = RefreshToken(refresh_token)
                token.blacklist()
                
                # Also revoke from our custom model if exists
                CustomRefreshToken.objects.filter(
                    user=request.user,
                    token=refresh_token
                ).update(is_revoked=True)
            else:
                # Revoke all refresh tokens for the user
                CustomRefreshToken.objects.filter(user=request.user).update(is_revoked=True)
            
            # Deactivate user sessions
            UserSession.objects.filter(user=request.user).update(is_active=False)
            
            logger.info(f"User logged out: {request.user.email}")
            
            return Response({
                'message': 'Logged out successfully.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Logout error for user {request.user.email}: {str(e)}")
            return Response({
                'message': 'Logged out successfully.'
            }, status=status.HTTP_200_OK)


class UserSessionsView(generics.ListAPIView):
    """List user's active sessions"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        sessions = UserSession.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-last_activity')
        
        session_data = []
        for session in sessions:
            session_data.append({
                'id': session.id,
                'device_info': session.device_info,
                'location': session.location,
                'ip_address': session.ip_address,
                'created_at': session.created_at,
                'last_activity': session.last_activity,
                'is_current': session.ip_address == get_client_ip(request)
            })
        
        return Response(session_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def revoke_session(request, session_id):
    """Revoke a specific user session"""
    try:
        session = UserSession.objects.get(
            id=session_id,
            user=request.user
        )
        session.is_active = False
        session.save()
        
        return Response({
            'message': 'Session revoked successfully.'
        }, status=status.HTTP_200_OK)
        
    except UserSession.DoesNotExist:
        return Response({
            'error': 'Session not found.'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """Get user statistics"""
    user = request.user
    
    # Import Task model to get task statistics
    from tasks.models import Task
    
    stats = {
        'profile': {
            'full_name': user.full_name,
            'email': user.email,
            'username': user.username,
            'date_joined': user.date_joined,
            'is_verified': user.is_verified,
        },
        'tasks': {
            'total_tasks': Task.objects.filter(user=user).count(),
            'completed_tasks': Task.objects.filter(user=user, status='done').count(),
            'pending_tasks': Task.objects.filter(user=user, status__in=['inbox', 'next']).count(),
            'overdue_tasks': len([t for t in Task.objects.filter(user=user) if t.is_overdue]),
        },
        'activity': {
            'recent_logins': LoginAttempt.objects.filter(
                email=user.email,
                success=True
            ).order_by('-attempted_at')[:5],
            'active_sessions': UserSession.objects.filter(
                user=user,
                is_active=True
            ).count(),
        }
    }
    
    return Response(stats, status=status.HTTP_200_OK)
