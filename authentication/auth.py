from .email_service import EmailService
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import login
from django.utils import timezone
from django.db import transaction
from .models import User, RefreshToken as CustomRefreshToken, LoginAttempt, UserSession, EmailVerificationToken, PasswordResetToken
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetSerializer,
    EmailVerificationSerializer,
    UserSerializer
)
import secrets
import uuid
from django.conf import settings


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            with transaction.atomic():
                user = serializer.save()
                
                # Create email verification token
                verification_token = EmailVerificationToken.objects.create(
                    user=user,
                    token=secrets.token_urlsafe(32)
                )
                
                EmailService.send_verification_email(user, verification_token)
                
                return Response({
                    'message': 'Registration successful. Please check your email to verify your account.',
                    'user': UserSerializer(user).data
                }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Log login attempt
        login_attempt = LoginAttempt.objects.create(
            email=request.data.get('email', ''),
            ip_address=ip_address,
            user_agent=user_agent,
            success=False
        )
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Store custom refresh token
            custom_refresh_token = CustomRefreshToken.objects.create(
                user=user,
                token=str(refresh),
                device_info=self.get_device_info(user_agent),
                ip_address=ip_address
            )
            
            # Create/update session
            session_key = str(uuid.uuid4())
            UserSession.objects.update_or_create(
                user=user,
                session_key=session_key,
                defaults={
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'device_info': self.get_device_info(user_agent),
                    'last_activity': timezone.now()
                }
            )
            
            # Update login attempt as successful
            login_attempt.success = True
            login_attempt.save()
            
            # Update user last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            return Response({
                'access_token': str(access_token),
                'refresh_token': str(refresh),
                'user': UserSerializer(user).data,
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        
        # Log failure reason
        login_attempt.failure_reason = str(serializer.errors)
        login_attempt.save()
        
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_device_info(self, user_agent):
        if 'Mobile' in user_agent:
            return 'Mobile'
        elif 'Tablet' in user_agent:
            return 'Tablet'
        else:
            return 'Desktop'


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            return Response({
                'error': 'Invalid or expired refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        access_token = serializer.validated_data['access']
        refresh_token = request.data.get('refresh')
        
        # Update the custom refresh token's last activity
        try:
            custom_token = CustomRefreshToken.objects.get(token=refresh_token)
            # Create new custom refresh token if rotation is enabled
            if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS'):
                custom_token.revoke()
                # The new refresh token would be handled by the JWT library
        except CustomRefreshToken.DoesNotExist:
            pass
        
        return Response({
            'access_token': access_token,
            'refresh_token': refresh_token if not settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS') else serializer.validated_data.get('refresh', refresh_token)
        }, status=status.HTTP_200_OK)


class ValidateTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        
        if not token:
            return Response({
                'valid': False,
                'error': 'Token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)
            
            return Response({
                'valid': True,
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        except TokenError:
            return Response({
                'valid': False,
                'error': 'Invalid or expired token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({
                'valid': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        
        if refresh_token:
            try:
                # Blacklist the refresh token
                token = RefreshToken(refresh_token)
                token.blacklist()
                
                # Revoke custom refresh token
                custom_token = CustomRefreshToken.objects.get(token=refresh_token)
                custom_token.revoke()
                
                # Deactivate session
                UserSession.objects.filter(user=request.user).update(is_active=False)
                
            except (TokenError, CustomRefreshToken.DoesNotExist):
                pass
        
        return Response({
            'message': 'Successfully logged out'
        }, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            
            # Invalidate existing reset tokens
            PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
            
            # Create new reset token
            reset_token = PasswordResetToken.objects.create(
                user=user,
                token=secrets.token_urlsafe(32),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            EmailService.send_password_reset_email(user, reset_token)
            
            return Response({
                'message': 'Password reset instructions sent to your email'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        
        if serializer.is_valid():
            reset_token = serializer.validated_data['reset_token']
            new_password = serializer.validated_data['new_password']
            
            # Reset password
            user = reset_token.user
            user.set_password(new_password)
            user.save()
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.save()
            
            # Revoke all existing tokens for security
            CustomRefreshToken.objects.filter(user=user).update(is_revoked=True)
            
            return Response({
                'message': 'Password reset successful'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        
        if serializer.is_valid():
            token = serializer.validated_data['token']
            
            try:
                verification_token = EmailVerificationToken.objects.get(token=token)
                
                if not verification_token.is_valid:
                    return Response({
                        'error': 'Invalid or expired verification token'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Verify user
                user = verification_token.user
                user.is_verified = True
                user.save()
                
                # Mark token as used
                verification_token.is_used = True
                verification_token.save()
                
                return Response({
                    'message': 'Email verified successfully'
                }, status=status.HTTP_200_OK)
                
            except EmailVerificationToken.DoesNotExist:
                return Response({
                    'error': 'Invalid verification token'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
