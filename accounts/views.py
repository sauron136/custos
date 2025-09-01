from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from django.db import transaction

from .models import UserProfile
from .serializers import UserProfileSerializer


class UserProfileViewSet(viewsets.ModelViewSet):
    """User profile management"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Get or create user profile"""
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def list(self, request, *args, **kwargs):
        """Return single profile object instead of list"""
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
