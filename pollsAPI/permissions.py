from rest_framework import permissions
import logging
from rest_framework.authtoken.models import Token
from .models import Poll

class PollsPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return True if view.action in ['list', 'retrieve'] else request.user.is_authenticated


    def has_object_permission(self, request, view, obj):
        if view.action in ['update', 'partial_update', 'delete', 'choices']:
            return request.user == obj.owner
        return super().has_object_permission(request, view, obj)
    
class ChoicePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in ['create', 'update', 'partial_update', 'delete']:
            poll_id= request.data['poll']
            poll = Poll.objects.get(id = poll_id)
            if poll:
                if poll.owner == request.user:
                    return True
            return False
        return False


    def has_object_permission(self, request, view, obj):
        if view.action in ['update', 'partial_update', 'delete']:
            return request.user == obj.poll.owner
        return super().has_object_permission(request, view, obj)
    


class UsersPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return True if view.action in ['create', 'ownPolls'] else request.user.is_authenticated


    def has_object_permission(self, request, view, obj):
        if view.action in ['retrieve', 'destroy', 'votedPolls']:
            return request.user == obj
        return super().has_object_permission(request, view, obj)