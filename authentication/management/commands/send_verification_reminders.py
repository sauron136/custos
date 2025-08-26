from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from authentication.models import EmailVerificationToken
import secrets

User = get_user_model()


class Command(BaseCommand):
    help = 'Send verification reminders to unverified users'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days-old',
            type=int,
            default=1,
            help='Send reminders to users registered N days ago (default: 1)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show who would receive reminders without actually sending',
        )
    
    def handle(self, *args, **options):
        days_old = options['days_old']
        dry_run = options['dry_run']
        
        # Find unverified users registered N days ago
        cutoff_date = timezone.now() - timedelta(days=days_old)
        unverified_users = User.objects.filter(
            is_verified=False,
            is_active=True,
            date_joined__date=cutoff_date.date()
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would send verification reminders to {unverified_users.count()} users'
                )
            )
            for user in unverified_users:
                self.stdout.write(f'  - {user.email}')
            return
        
        sent_count = 0
        for user in unverified_users:
            try:
                # Generate new verification token
                token = secrets.token_urlsafe(50)
                EmailVerificationToken.objects.create(
                    user=user,
                    token=token
                )
                
                # Send reminder email
                subject = 'Reminder: Verify your email address'
                message = render_to_string('emails/verification_reminder.html', {
                    'user': user,
                    'verification_url': f"{settings.FRONTEND_URL}/verify/{token}",
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
                
                sent_count += 1
                self.stdout.write(f'Sent reminder to {user.email}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to send reminder to {user.email}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully sent {sent_count} verification reminders')
        )

