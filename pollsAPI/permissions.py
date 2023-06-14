from rest_framework import permissions
import logging
from rest_framework.authtoken.models import Token
from .models import Poll

class PollsPermission(permissions.BasePermission):
    owner = ['update', 'partial_update', 'destroy', 'choices']
    generale = ['list', 'retrieve']
    auth = ['create']
    permessi = {tuple(owner) : "L'utente che effettua la richiesta deve essere il proprietario del sondaggio",
                tuple(generale): "Nessun permesso necessario",
                tuple(auth): "È necessario autenticarsi per effettuare la richiesta"}
    @classmethod
    def get_permission_string(cls, action):
        for key, value in cls.permessi.items():
            if action in key:
                return value
        return "Permesso non definito per questa azione"

    def has_permission(self, request, view):
        return True if view.action in self.generale else request.user.is_authenticated


    def has_object_permission(self, request, view, obj):
        if view.action in self.owner:
            return request.user == obj.owner
        return super().has_object_permission(request, view, obj)
    
class ChoicePermission(permissions.BasePermission):
    owner = ['create', 'update', 'partial_update', 'destroy']
    generale = ['list', 'retrieve']
    auth = ['vote']
    permessi = {tuple(owner) : "L'utente che effettua la richiesta deve essere il proprietario del sondaggio a cui appartiene la scelta",
                tuple(generale): "Nessun permesso necessario",
                tuple(auth): "È necessario autenticarsi per effettuare la richiesta"}
    @classmethod
    def get_permission_string(cls, action):
        for key, value in cls.permessi.items():
            if action in key:
                return value
        return "Permesso non definito per questa azione"
    
    def has_permission(self, request, view):
        if view.action in self.owner:
            poll_id= request.data['poll']
            poll = Poll.objects.get(id = poll_id)
            if poll:
                if poll.owner == request.user:
                    return True
            return False
        return True


    def has_object_permission(self, request, view, obj):
        if view.action in self.owner:
            return request.user == obj.poll.owner
        elif view.action in self.auth:
            return request.user.is_authenticated
        return super().has_object_permission(request, view, obj)
    


class UsersPermission(permissions.BasePermission):
    
    generale = ['create', 'list', 'ownPolls']
    owner = ['retrieve', 'destroy', 'votedPolls']
    permessi = {tuple(owner) : "Solamente l'utente interessato può effettuare questa richiesta",
                tuple(generale): "Nessun permesso necessario"}
    @classmethod
    def get_permission_string(cls, action):
        for key, value in cls.permessi.items():
            if action in key:
                return value
        return "Permesso non definito per questa azione"

    def has_permission(self, request, view):
        return True if view.action in self.generale else request.user.is_authenticated


    def has_object_permission(self, request, view, obj):
        if view.action in self.owner:
            return request.user == obj
        return super().has_object_permission(request, view, obj)