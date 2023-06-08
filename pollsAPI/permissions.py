from rest_framework import permissions
import logging
from rest_framework.authtoken.models import Token

class PollsPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in ['list', 'retrieve', 'choices']:
            return True
        else:
            return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj)