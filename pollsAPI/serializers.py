import sys
from django.contrib.auth.models import User, Group
from django.urls import reverse
from rest_framework import serializers
from .models import Poll, Choice
from django.utils import timezone
from rest_framework.validators import UniqueValidator

class UserSerializer(serializers.HyperlinkedModelSerializer):
    username = serializers.CharField(validators = [
        UniqueValidator(
            queryset=User.objects.all(),
            message='Questo username è già stato utilizzato'
        )
    ])
    email = serializers.EmailField(validators = [
        UniqueValidator(
            queryset=User.objects.all(),
            message='Questa email è già stata utilizzata'
        )
    ])
    class Meta:
        model = User
        fields = ['url', 'username', 'password', 'email']



"""class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']"""

class PollSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Poll
        fields = ['url', 'question_text', 'pub_date']

class ChoiceSerializer(serializers.HyperlinkedModelSerializer):
    votes = serializers.SerializerMethodField()
    users = serializers.HyperlinkedRelatedField(
        many=True,
        queryset=User.objects.all(),
        view_name='user-detail'
    )
    class Meta:
        model = Choice
        fields = ['url', 'poll', 'choice_text', 'users', 'votes']
    def get_votes(self, obj):
        return obj.users.count()


        
