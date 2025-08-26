from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Count, Q
from tasks.models import Task, Project
import csv
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate user activity reports'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--period',
            type=str,
            choices=['daily', 'weekly', 'monthly'],
            default='weekly',
            help='Report period (default: weekly)',
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='reports',
            help='Output directory for reports (default: reports)',
        )
    
    def handle(self, *args, **options):
        period = options['period']
        output_dir = options['output_dir']
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Calculate date range
        now = timezone.now()
        if period == 'daily':
            start_date = now - timedelta(days=1)
        elif period == 'weekly':
            start_date = now - timedelta(weeks=1)
        else:  # monthly
            start_date = now - timedelta(days=30)
        
        # Generate report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'user_activity_report_{period}_{timestamp}.csv'
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'User Email', 'Full Name', 'Total Tasks', 'Completed Tasks',
                'Active Projects', 'Last Login', 'Registration Date', 'Is Verified'
            ])
            
            # Get user data
            users = User.objects.filter(is_active=True).order_by('date_joined')
            
            for user in users:
                total_tasks = Task.objects.filter(user=user).count()
                completed_tasks = Task.objects.filter(
                    user=user, 
                    status='done',
                    completed_at__gte=start_date
                ).count()
                active_projects = Project.objects.filter(
                    user=user, 
                    is_active=True
                ).count()
                
                writer.writerow([
                    user.email,
                    user.full_name,
                    total_tasks,
                    completed_tasks,
                    active_projects,
                    user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
                    user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                    'Yes' if user.is_verified else 'No'
                ])
        
        self.stdout.write(
            self.style.SUCCESS(f'User activity report generated: {filepath}')
        )

