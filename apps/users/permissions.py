from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to access/edit it.
    Assumes the model instance has a `user` attribute.
    """

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        # Admin / staff users have global read access if needed, or strict ownership
        if request.user.is_staff or request.user.is_superuser:
            return True
        return hasattr(obj, "user") and obj.user == request.user


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission allowing full access to admins, and owner-only access to regular users.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        if request.user.is_staff or request.user.is_superuser:
            return True
        return hasattr(obj, "user") and obj.user == request.user
