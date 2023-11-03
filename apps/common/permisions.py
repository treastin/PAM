from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.users.models import User


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == User.Role.ADMIN


class IsAdminOrOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (request.user.role == User.Role.ADMIN) | (obj.user == request.user)


class IsAdminOrItself(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (request.user.role == User.Role.ADMIN) | (obj == request.user)


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
