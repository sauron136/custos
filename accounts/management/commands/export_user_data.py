from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core import serializers
import json
import os
from datetime import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'Export user data for backup or migration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Export data for specific user email',
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='exports',
            help='Output directory for exports (default: exports)',
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'xml'],
            default='json',
            help='Export format (default: json)',
        )
    
    def handle(self, *args, **options):
        output_dir = options['output_dir']
        export_format = options['format']
        user_email = options.get('user_email')
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        if user_email:
            try:
                user = User.objects.get(email=user_email)
                self.export_user_data(user, output_dir, export_format)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with email {user_email} not found')
                )
                return
        else:
            # Export all users
            users = User.objects.all()
            for user in users:
                self.export_user_data(user, output_dir, export_format)
        
        self.stdout.write(
            self.style.SUCCESS('Export completed successfully')
        )
    
    def export_user_data(self, user, output_dir, export_format):
        """Export data for a specific user"""
        from tasks.models import Task, Project, Context
        from accounts.models import UserProfile, UserPreferences, UserNotificationSettings
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"user_{user.id}_{timestamp}.{export_format}"
        filepath = os.path.join(output_dir, filename)
        
        # Gather related data
        tasks = Task.objects.filter(user=user)
        projects = Project.objects.filter(user=user)
        contexts = Context.objects.filter(user=user)
        
        try:
            profile = user.profile
        except:
            profile = None
        
        try:
            preferences = user.preferences
        except:
            preferences = None
        
        try:
            notification_settings = user.notification_settings
        except:
            notification_settings = None
        
        # Create data structure
        data = {
            'user': [user],
            'tasks': list(tasks),
            'projects': list(projects),
            'contexts': list(contexts),
        }
        
        if profile:
            data['profile'] = [profile]
        if preferences:
            data['preferences'] = [preferences]
        if notification_settings:
            data['notification_settings'] = [notification_settings]
        
        # Export data
        with open(filepath, 'w') as f:
            if export_format == 'json':
                # Convert to JSON serializable format
                json_data = {}
                for key, queryset in data.items():
                    json_data[key] = json.loads(serializers.serialize('json', queryset))
                
                json.dump(json_data, f, indent=2, default=str)
            else:
                # XML format
                for key, queryset in data.items():
                    f.write(f'<!-- {key.upper()} -->\n')
                    f.write(serializers.serialize('xml', queryset))
                    f.write('\n\n')
        
        self.stdout.write(f'Exported data for {user.email} to {filepath}')

