# authentication/utils.py
import re
import secrets
import string
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_device_info(user_agent):
    """Extract device information from user agent string"""
    if not user_agent:
        return 'Unknown Device'
    
    # Mobile devices
    if re.search(r'Mobile|Android|iPhone|iPad', user_agent, re.I):
        if 'iPhone' in user_agent:
            return 'iPhone'
        elif 'iPad' in user_agent:
            return 'iPad'
        elif 'Android' in user_agent:
            return 'Android Device'
        else:
            return 'Mobile Device'
    
    # Desktop browsers
    if 'Chrome' in user_agent:
        return 'Chrome Browser'
    elif 'Firefox' in user_agent:
        return 'Firefox Browser'
    elif 'Safari' in user_agent:
        return 'Safari Browser'
    elif 'Edge' in user_agent:
        return 'Edge Browser'
    
    return 'Desktop Browser'


def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    digits = string.digits
    return ''.join(secrets.choice(digits) for _ in range(length))


def generate_secure_token(length=50):
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)


def is_password_strong(password):
    """Check if password meets strength requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    # Check for common passwords
    common_passwords = [
        'password', '123456', '12345678', 'qwerty', 'abc123',
        'password123', 'admin', 'letmein', 'welcome', 'monkey'
    ]
    
    if password.lower() in common_passwords:
        return False, "Password is too common"
    
    return True, "Password is strong"


def send_email_async(subject, template_name, context, recipient_list, from_email=None):
    """Send email asynchronously with error handling"""
    try:
        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL
        
        html_message = render_to_string(template_name, context)
        
        send_mail(
            subject=subject,
            message='',  # Plain text version (optional)
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Email sent successfully to {', '.join(recipient_list)}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {', '.join(recipient_list)}: {str(e)}")
        return False


def validate_email_domain(email):
    """Validate email domain against allowed/blocked domains"""
    domain = email.split('@')[1].lower()
    
    # Check blocked domains
    blocked_domains = getattr(settings, 'BLOCKED_EMAIL_DOMAINS', [])
    if domain in blocked_domains:
        return False, f"Email domain '{domain}' is not allowed"
    
    # Check allowed domains (if specified)
    allowed_domains = getattr(settings, 'ALLOWED_EMAIL_DOMAINS', [])
    if allowed_domains and domain not in allowed_domains:
        return False, f"Email domain '{domain}' is not allowed"
    
    return True, "Domain is valid"


def check_rate_limit(identifier, limit=5, window_minutes=15):
    """Check if an action is rate limited for an identifier"""
    from django.core.cache import cache
    
    cache_key = f"rate_limit:{identifier}"
    current_count = cache.get(cache_key, 0)
    
    if current_count >= limit:
        return False, f"Rate limit exceeded. Try again in {window_minutes} minutes."
    
    # Increment counter
    cache.set(cache_key, current_count + 1, timeout=window_minutes * 60)
    
    return True, f"Action allowed. {limit - current_count - 1} attempts remaining."


def is_suspicious_activity(user, ip_address, user_agent):
    """Check for suspicious login activity"""
    from .models import LoginAttempt, UserSession
    
    # Check for multiple failed attempts from same IP
    recent_failures = LoginAttempt.objects.filter(
        ip_address=ip_address,
        success=False,
        attempted_at__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    if recent_failures >= 5:
        return True, "Multiple failed login attempts from this IP"
    
    # Check for login from new location/device
    if user:
        previous_sessions = UserSession.objects.filter(
            user=user,
            ip_address=ip_address
        ).exists()
        
        if not previous_sessions:
            # New IP address for this user
            return True, "Login from new location"
    
    return False, "Activity appears normal"


def cleanup_expired_tokens():
    """Clean up expired tokens (run as periodic task)"""
    from .models import EmailVerificationToken, PasswordResetToken, CustomRefreshToken
    
    now = timezone.now()
    
    # Clean expired verification tokens
    expired_verification = EmailVerificationToken.objects.filter(
        expires_at__lt=now
    ).delete()
    
    # Clean expired reset tokens
    expired_reset = PasswordResetToken.objects.filter(
        expires_at__lt=now
    ).delete()
    
    # Clean expired refresh tokens
    expired_refresh = CustomRefreshToken.objects.filter(
        expires_at__lt=now
    ).delete()
    
    logger.info(f"Cleaned up expired tokens: {expired_verification[0]} verification, "
                f"{expired_reset[0]} reset, {expired_refresh[0]} refresh")


def create_user_activity_log(user, action, ip_address, user_agent, details=None):
    """Create a log entry for user activities"""
    from .models import UserActivityLog
    
    try:
        UserActivityLog.objects.create(
            user=user,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            timestamp=timezone.now()
        )
    except Exception as e:
        logger.error(f"Failed to create activity log: {str(e)}")


def mask_email(email):
    """Mask email for security purposes"""
    if '@' not in email:
        return email
    
    username, domain = email.split('@')
    
    if len(username) <= 2:
        masked_username = '*' * len(username)
    else:
        masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
    
    return f"{masked_username}@{domain}"


def generate_username_suggestions(email, first_name=None, last_name=None):
    """Generate username suggestions based on email and name"""
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    suggestions = []
    
    # Base username from email
    base = email.split('@')[0]
    suggestions.append(base)
    
    # Add variations with name
    if first_name and last_name:
        name_combinations = [
            f"{first_name.lower()}{last_name.lower()}",
            f"{first_name.lower()}.{last_name.lower()}",
            f"{first_name.lower()[0]}{last_name.lower()}",
            f"{first_name.lower()}{last_name.lower()[0]}",
        ]
        suggestions.extend(name_combinations)
    
    # Add numbers if username exists
    available_suggestions = []
    for suggestion in suggestions[:5]:  # Limit to 5 base suggestions
        if not User.objects.filter(username=suggestion).exists():
            available_suggestions.append(suggestion)
        else:
            # Try with numbers
            for i in range(1, 10):
                numbered_suggestion = f"{suggestion}{i}"
                if not User.objects.filter(username=numbered_suggestion).exists():
                    available_suggestions.append(numbered_suggestion)
                    break
    
    return available_suggestions[:5]  # Return max 5 suggestions
