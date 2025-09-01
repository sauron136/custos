# account/filters.py
import django_filters
from django.db.models import Q
from django.utils import timezone
from .models import Task


class TaskFilter(django_filters.FilterSet):
    """Comprehensive task filtering"""
    
    # Status and priority filters
    status = django_filters.MultipleChoiceFilter(choices=Task.STATUS_CHOICES)
    priority = django_filters.MultipleChoiceFilter(choices=Task.PRIORITY_CHOICES)
    
    # Relationship filters
    project = django_filters.UUIDFilter(field_name='project__id')
    category = django_filters.UUIDFilter(field_name='category__id')
    tags = django_filters.BaseInFilter(field_name='tags__id')
    assigned_to = django_filters.UUIDFilter(field_name='assigned_to__id')
    
    # Boolean filters
    is_favorite = django_filters.BooleanFilter()
    has_subtasks = django_filters.BooleanFilter(method='filter_has_subtasks')
    has_attachments = django_filters.BooleanFilter(method='filter_has_attachments')
    is_recurring = django_filters.BooleanFilter(method='filter_is_recurring')
    
    # Date filters
    due_date = django_filters.DateFilter(field_name='due_date__date')
    due_date_from = django_filters.DateTimeFilter(field_name='due_date', lookup_expr='gte')
    due_date_to = django_filters.DateTimeFilter(field_name='due_date', lookup_expr='lte')
    created_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    completed_from = django_filters.DateTimeFilter(field_name='completed_at', lookup_expr='gte')
    completed_to = django_filters.DateTimeFilter(field_name='completed_at', lookup_expr='lte')
    
    # Text search
    search = django_filters.CharFilter(method='filter_search')
    
    # Special filters
    overdue = django_filters.BooleanFilter(method='filter_overdue')
    due_today = django_filters.BooleanFilter(method='filter_due_today')
    due_this_week = django_filters.BooleanFilter(method='filter_due_this_week')
    no_due_date = django_filters.BooleanFilter(method='filter_no_due_date')
    completed = django_filters.BooleanFilter(method='filter_completed')
    
    class Meta:
        model = Task
        fields = []
    
    def filter_has_subtasks(self, queryset, name, value):
        """Filter tasks that have subtasks"""
        if value:
            return queryset.filter(subtasks__isnull=False).distinct()
        return queryset.filter(subtasks__isnull=True)
    
    def filter_has_attachments(self, queryset, name, value):
        """Filter tasks that have attachments"""
        if value:
            return queryset.filter(attachments__isnull=False).distinct()
        return queryset.filter(attachments__isnull=True)
    
    def filter_is_recurring(self, queryset, name, value):
        """Filter recurring tasks"""
        if value:
            return queryset.exclude(recurrence_pattern='')
        return queryset.filter(recurrence_pattern='')
    
    def filter_search(self, queryset, name, value):
        """Search in task title, description, and notes"""
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(notes__icontains=value) |
            Q(tags__name__icontains=value)
        ).distinct()
    
    def filter_overdue(self, queryset, name, value):
        """Filter overdue tasks"""
        now = timezone.now()
        if value:
            return queryset.filter(
                due_date__lt=now,
                status__in=['todo', 'in_progress']
            )
        return queryset.exclude(
            due_date__lt=now,
            status__in=['todo', 'in_progress']
        )
    
    def filter_due_today(self, queryset, name, value):
        """Filter tasks due today"""
        today = timezone.now().date()
        if value:
            return queryset.filter(due_date__date=today)
        return queryset.exclude(due_date__date=today)
    
    def filter_due_this_week(self, queryset, name, value):
        """Filter tasks due this week"""
        now = timezone.now()
        week_start = now.date() - timezone.timedelta(days=now.weekday())
        week_end = week_start + timezone.timedelta(days=6)
        
        if value:
            return queryset.filter(due_date__date__range=[week_start, week_end])
        return queryset.exclude(due_date__date__range=[week_start, week_end])
    
    def filter_no_due_date(self, queryset, name, value):
        """Filter tasks without due date"""
        if value:
            return queryset.filter(due_date__isnull=True)
        return queryset.filter(due_date__isnull=False)
    
    def filter_completed(self, queryset, name, value):
        """Filter completed tasks"""
        if value:
            return queryset.filter(status='completed')
        return queryset.exclude(status='completed')


class ProjectFilter(django_filters.FilterSet):
    """Project filtering"""
    
    status = django_filters.MultipleChoiceFilter(field_name='status')
    search = django_filters.CharFilter(method='filter_search')
    has_tasks = django_filters.BooleanFilter(method='filter_has_tasks')
    
    class Meta:
        model = Task  # This should reference Project model when it's defined
        fields = []
    
    def filter_search(self, queryset, name, value):
        """Search in project name and description"""
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )
    
    def filter_has_tasks(self, queryset, name, value):
        """Filter projects that have tasks"""
        if value:
            return queryset.filter(tasks__isnull=False).distinct()
        return queryset.filter(tasks__isnull=True)


class CategoryFilter(django_filters.FilterSet):
    """Category filtering"""
    
    search = django_filters.CharFilter(method='filter_search')
    has_tasks = django_filters.BooleanFilter(method='filter_has_tasks')
    
    class Meta:
        model = Task  # This should reference Category model when it's defined
        fields = []
    
    def filter_search(self, queryset, name, value):
        """Search in category name"""
        return queryset.filter(name__icontains=value)
    
    def filter_has_tasks(self, queryset, name, value):
        """Filter categories that have tasks"""
        if value:
            return queryset.filter(tasks__isnull=False).distinct()
        return queryset.filter(tasks__isnull=True)
