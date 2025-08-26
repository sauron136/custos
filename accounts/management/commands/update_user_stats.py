from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tasks.models import Task, Project
from accounts.models import UserActivityLog

User = get_user_model()


class Command(BaseCommand):
    help = 'Update user statistics and generate activity summaries'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=str,
            help='Update stats for specific user ID',
        )
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Update stats for all users',
        )
    
    def handle(self, *args, **options):
        if options['user_id']:
            try:
                user = User.objects.get(id=options['user_id'])
                self.update_user_stats(user)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {options["user_id"]} not found')
                )
                return
        elif options['all_users']:
            users = User.objects.filter(is_active=True)
            for user in users:
                self.update_user_stats(user)
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --user-id or --all-users')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS('Successfully updated user statistics')
        )
    
    def update_user_stats(self, user):
        """Update statistics for a specific user"""
        # Count tasks
        total_tasks = Task.objects.filter(user=user).count()
        completed_tasks = Task.objects.filter(user=user, status='done').count()
        
        # Count projects
        total_projects = Project.objects.filter(user=user).count()
        active_projects = Project.objects.filter(user=user, is_active=True).count()
        
        # Log activity summary
        UserActivityLog.objects.create(
            user=user,
            action='stats_update',
            description='Automated statistics update',
            details={
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'total_projects': total_projects,
                'active_projects': active_projects,
            }
        )
        
        self.stdout.write(f'Updated stats for {user.email}')
