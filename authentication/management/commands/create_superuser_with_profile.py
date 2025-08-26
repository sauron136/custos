from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import UserProfile, UserPreferences, UserNotificationSettings

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser with complete profile setup'
    
    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Superuser email', required=True)
        parser.add_argument('--password', type=str, help='Superuser password', required=True)
        parser.add_argument('--first-name', type=str, help='First name', required=True)
        parser.add_argument('--last-name', type=str, help='Last name', required=True)
        parser.add_argument('--username', type=str, help='Username (optional)')
    
    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        username = options.get('username') or email.split('@')[0]
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.ERROR(f'User with email {email} already exists')
            )
            return
        
        # Create superuser
        user = User.objects.create_superuser(
            email=email,
            password=password,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create profile
        UserProfile.objects.create(user=user)
        
        # Create preferences
        UserPreferences.objects.create(user=user)
        
        # Create notification settings
        UserNotificationSettings.objects.create(user=user)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created superuser {email} with complete profile'
            )
        )

