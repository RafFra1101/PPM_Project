

# Create your views here.
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, renderers
from rest_framework import permissions, authentication
from pollsAPI.serializers import *
from .models import Question, Choice

from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response

import logging


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

class PollViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows polls to be viewed or edited.
    """
    queryset = Question.objects.all().order_by('-pub_date')
    serializer_class = QuestionSerializer
    #permission_classes = [permissions.IsAuthenticated]

    # use list_route decorator
    @action(detail=True)
    def choices(self, request, pk=None):
        """
        Returns a list of all the group names that the given
        user belongs to.
        """
        poll = self.get_object()
        choices = Choice.objects.filter(question = poll)
        choices_data = [{'URL sondaggio' : QuestionSerializer(poll, context={'request':request}).data['url']}]
        for choice in choices:
            choices_data.append({
                'URL': ChoiceSerializer(choice, context={'request':request}).data['url'],
                'Testo': choice.choice_text,
                'Voti': choice.votes 
            })
        return Response(choices_data)


class ChoiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows polls to be viewed or edited.
    """
    queryset = Choice.objects.all()
    serializer_class = ChoiceSerializer
    #permission_classes = [permissions.IsAuthenticated]


class PollDetailView(APIView):
    """
    View to list poll details.

    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = QuestionSerializer

    model = Question

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())
    



