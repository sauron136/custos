from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def send_verification_email(user, verification_token):
        """Send email verification email"""
        try:
            subject = 'Verify Your Email Address'
            
            # Create verification URL (adjust domain as needed)
            verification_url = f"http://localhost:8000/api/auth/email/verify/?token={verification_token.token}"
            
            context = {
                'user': user,
                'verification_url': verification_url,
                'token': verification_token.token
            }
            
            # Render HTML email template
            html_message = render_to_string('emails/email_verification.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Verification email sent to {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
    
    @staticmethod
    def send_password_reset_email(user, reset_token):
        """Send password reset email"""
        try:
            subject = 'Reset Your Password'
            
            # Create reset URL (adjust domain as needed)
            reset_url = f"http://localhost:8000/password-reset/?token={reset_token.token}"
            
            context = {
                'user': user,
                'reset_url': reset_url,
                'token': reset_token.token
            }
            
            html_message = render_to_string('emails/password_reset.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Password reset email sent to {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
