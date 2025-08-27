from rest_framework import permissions

class IsOwnerPermission(permissions.BasePermission):
    """
    Permission to only allow owners of an object to view/edit it.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
