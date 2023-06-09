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
    users = serializers.HyperlinkedRelatedField(
        many=True,
        queryset=User.objects.all(),
        view_name='user-detail'
    )
    class Meta:
        model = Poll
        fields = ['url', 'question_text', 'pub_date', 'users']

class ChoiceSerializer(serializers.HyperlinkedModelSerializer):
    poll = serializers.PrimaryKeyRelatedField(
        queryset = Poll.objects.all(),
        many = False
    )
    class Meta:
        model = Choice
        fields = ['url', 'poll', 'choice_text', 'votes']
    def update(self, instance, validated_data):
        instance.poll = validated_data.get('poll')
        instance.choice_text = validated_data.get('choice_text', instance.choice_text)
        instance.votes = validated_data.get('votes', instance.votes)
        instance.save()
        return instance
    
    def partial_update(self, instance, validated_data):
        # Aggiorna solo i campi presenti nei dati validati
        for field, value in validated_data.items():
            if field == "poll":
                instance.poll = validated_data.get('poll')
            else :
                setattr(instance, field, value)

        instance.save()
        return instance


        
