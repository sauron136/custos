from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import EmailVerificationToken, PasswordResetToken, RefreshToken


class Command(BaseCommand):
    help = 'Clean up expired authentication tokens'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
    
    def handle(self, *args, **options):
        now = timezone.now()
        dry_run = options['dry_run']
        
        # Count expired tokens
        expired_verification = EmailVerificationToken.objects.filter(expires_at__lt=now)
        expired_reset = PasswordResetToken.objects.filter(expires_at__lt=now)
        expired_refresh = RefreshToken.objects.filter(expires_at__lt=now)
        
        verification_count = expired_verification.count()
        reset_count = expired_reset.count()
        refresh_count = expired_refresh.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {verification_count} verification tokens, '
                    f'{reset_count} reset tokens, and {refresh_count} refresh tokens'
                )
            )
        else:
            # Delete expired tokens
            expired_verification.delete()
            expired_reset.delete()
            expired_refresh.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {verification_count} verification tokens, '
                    f'{reset_count} reset tokens, and {refresh_count} refresh tokens'
                )
            )
