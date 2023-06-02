import sys
from django.contrib.auth.models import User, Group
from django.urls import reverse
from rest_framework import serializers
from .models import Question, Choice
from django.utils import timezone

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

class QuestionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Question
        fields = ['url', 'question_text', 'pub_date']

class ChoiceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Choice
        fields = ['url', 'question', 'choice_text', 'votes']
        read_only_fields = ['url', 'question', 'choice_text']

        
