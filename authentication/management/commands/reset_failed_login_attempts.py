from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from authentication.models import LoginAttempt


class Command(BaseCommand):
    help = 'Reset failed login attempt counters'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Reset attempts for specific email address',
        )
        parser.add_argument(
            '--ip',
            type=str,
            help='Reset attempts for specific IP address',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Reset all failed login attempts older than 24 hours',
        )
    
    def handle(self, *args, **options):
        email = options.get('email')
        ip_address = options.get('ip')
        reset_all = options.get('all')
        
        if email:
            # Reset attempts for specific email
            attempts = LoginAttempt.objects.filter(
                email=email,
                success=False
            )
            count = attempts.count()
            attempts.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Reset {count} failed login attempts for {email}'
                )
            )
        
        elif ip_address:
            # Reset attempts for specific IP
            attempts = LoginAttempt.objects.filter(
                ip_address=ip_address,
                success=False
            )
            count = attempts.count()
            attempts.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Reset {count} failed login attempts for IP {ip_address}'
                )
            )
        
        elif reset_all:
            # Reset all attempts older than 24 hours
            cutoff_date = timezone.now() - timedelta(hours=24)
            attempts = LoginAttempt.objects.filter(
                success=False,
                attempted_at__lt=cutoff_date
            )
            count = attempts.count()
            attempts.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Reset {count} failed login attempts older than 24 hours'
                )
            )
        
        else:
            self.stdout.write(
                self.style.ERROR(
                    'Please specify --email, --ip, or --all'
                )
            )
