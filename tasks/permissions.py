from rest_framework import permissions

class IsOwnerPermission(permissions.BasePermission):
    """
    Permission to only allow owners of an object to view/edit it.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Anyone can view (read-only).
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the owner
        return obj.user == request.user


class CanEditProject(permissions.BasePermission):
    """
    Permission to allow project owners and collaborators to edit projects.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Check if user is the project owner
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # Check if user is a collaborator (assuming you have a collaborators relationship)
        if hasattr(obj, 'collaborators') and request.user in obj.collaborators.all():
            return True
        
        return False
