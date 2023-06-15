
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Poll, Choice
from rest_framework.validators import UniqueValidator
import bcrypt

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

    def create(self, validated_data):
        # Cripta la password utilizzando bcrypt
        password = validated_data.pop('password')
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        # Crea l'utente con la password criptata
        user = User.objects.create(
            password=hashed_password.decode(),
            **validated_data
        )
        return user

    class Meta:
        model = User
        fields = ['url', 'username', 'password', 'email']


class PollSerializer(serializers.HyperlinkedModelSerializer):
    
    class Meta:
        model = Poll
        fields = ['url', 'owner', 'question_text', 'pub_date']

    def partial_update(self, instance, validated_data):
        # Aggiorna solo i campi presenti nei dati validati
        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.save()
        return instance
    

class ChoiceSerializer(serializers.HyperlinkedModelSerializer):
    users = serializers.HyperlinkedRelatedField(
        many=True,
        queryset=User.objects.all(),
        view_name='user-detail',
        lookup_field = "username"
    )
    class Meta:
        model = Choice
        fields = ['url', 'poll', 'choice_text', 'votes', 'users']
    
    def update(self, instance, validated_data):
        instance.owner = validated_data.get('poll')
        instance.users.set(validated_data.get('users'))
        instance.choice_text = validated_data.get('choice_text', instance.choice_text)
        instance.votes = validated_data.get('votes', instance.votes)
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


        
