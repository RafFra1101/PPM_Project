import sys
from django.contrib.auth.models import User, Group
from django.urls import reverse
from rest_framework import serializers
from .models import Poll, Choice
from django.utils import timezone
from rest_framework.validators import UniqueValidator
import logging

class UserSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='user-detail',
        lookup_field='username'
    )
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


class PollSerializer(serializers.HyperlinkedModelSerializer):
    users = serializers.HyperlinkedRelatedField(
        many=True,
        queryset=User.objects.all(),
        view_name='user-detail',
        lookup_field = "username"
    )
    class Meta:
        model = Poll
        fields = ['url', 'question_text', 'pub_date', 'users']
    def update(self, instance, validated_data):
        instance.users.set(validated_data.get('users'))
        instance.question_text = validated_data.get('question_text', instance.question_text)
        instance.pub_date = validated_data.get('pub_date', instance.pub_date)
        instance.save()
        return instance
    def partial_update(self, instance, validated_data):
        # Aggiorna solo i campi presenti nei dati validati
        for field, value in validated_data.items():
            if field == 'users':
                instance.users.set(value)
            else:
                setattr(instance, field, value)

        instance.save()
        return instance
    

class ChoiceSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Choice
        fields = ['url', 'poll', 'choice_text', 'votes']
    
    def partial_update(self, instance, validated_data):
        # Aggiorna solo i campi presenti nei dati validati
        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.save()
        return instance


        
