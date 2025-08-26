# authentication/managers.py
from django.contrib.auth.models import BaseUserManager
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models

class CustomUserManager(BaseUserManager):
    """Custom manager for User model"""
    
    def _create_user(self, email, password, username=None, **extra_fields):
        """Create and save a user with the given email and password"""
        if not email:
            raise ValueError('The Email field must be set')
        
        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError('Invalid email address')
        
        # Normalize email
        email = self.normalize_email(email)
        
        # Generate username if not provided
        if not username:
            username = email.split('@')[0]
            # Ensure username is unique
            counter = 1
            original_username = username
            while self.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
        
        # Create user
        user = self.model(
            email=email,
            username=username,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password=None, **extra_fields):
        """Create a regular user"""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self._create_user(email, password, **extra_fields)
    
    def get_by_natural_key(self, username):
        """Allow login with email or username"""
        return self.get(
            models.Q(email__iexact=username) | models.Q(username__iexact=username)
        )
    
    def active_users(self):
        """Return only active users"""
        return self.filter(is_active=True)
    
    def verified_users(self):
        """Return only verified users"""
        return self.filter(is_verified=True)
    
    def unverified_users(self):
        """Return only unverified users"""
        return self.filter(is_verified=False)
    
    def recent_signups(self, days=7):
        """Return users who signed up in the last N days"""
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(date_joined__gte=cutoff_date)
    
    def search_users(self, query):
        """Search users by email, username, first_name, or last_name"""
        from django.db.models import Q
        return self.filter(
            Q(email__icontains=query) |
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    
    def bulk_create_users(self, user_data_list):
        """Bulk create users from a list of dictionaries"""
        users = []
        for user_data in user_data_list:
            email = user_data.pop('email')
            password = user_data.pop('password')
            user = self.create_user(email=email, password=password, **user_data)
            users.append(user)
        return users
