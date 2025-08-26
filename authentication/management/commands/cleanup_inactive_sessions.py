from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from authentication.models import UserSession


class Command(BaseCommand):
    help = 'Clean up inactive user sessions'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Remove sessions inactive for N days (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        inactive_sessions = UserSession.objects.filter(
            last_activity__lt=cutoff_date
        )
        
        count = inactive_sessions.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} inactive sessions older than {days} days'
                )
            )
        else:
            inactive_sessions.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {count} inactive sessions older than {days} days'
                )
            )

