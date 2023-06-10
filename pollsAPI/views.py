

# Create your views here.
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, renderers, permissions, authentication, status, mixins
from pollsAPI.serializers import *
from .models import Poll, Choice
from .permissions import PollsPermission, ChoicePermission, UsersPermission
from django.http import JsonResponse
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth.hashers import Argon2PasswordHasher, make_password, check_password
import logging, requests, bcrypt

logging.getLogger().setLevel(logging.INFO)
api_url = "http://127.0.0.1:8000/"
class UserViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    
    """API endpoint that allows users to be viewed or edited."""
    
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    lookup_field = 'username'
    authentication_classes = [TokenAuthentication]
    permission_classes = [UsersPermission]

    def list(self, request, *args, **kwargs):
        super_data = super().list(request, *args, **kwargs).data
        for i in super_data['results']:
            i.pop('password')
            i.pop('email')
        return Response(super_data)
    @action(methods = ["get"], detail = True)
    def ownPolls(self, request, username=None):
        polls = Poll.objects.filter(owner = username)
        serializer = PollSerializer(polls, many=True, context={'request':request})
        return Response(serializer.data)
    @action(methods = ["get"], detail = True)
    def votedPolls(self, request, username=None):
        polls = Poll.objects.filter(users__username = username)
        serializer = PollSerializer(polls, many=True, context={'request':request})
        return Response(serializer.data)
        

    


@swagger_auto_schema(method='post', request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['username', 'email', 'password'],
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING),
            'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
            'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD),
        },
        
))
@api_view(['POST'])
def register(request):
    if request.data.get('username') and request.data.get('password') and request.data.get('email'):
        try:
            serializer = UserSerializer(data=request.data, context = {'request': request})
            if serializer.is_valid():
                user = serializer.create(serializer.validated_data)
                logging.warning(user.password)
                token = Token.objects.create(user=user)
                logging.info(token.key)
                return Response(data={'token':token.key},status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status = 400)  
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    else:
        
        return Response({'error': 'Please provide username, password and email.'}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='post', request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['info', 'password'],
        properties={
            'info': openapi.Schema(type=openapi.TYPE_STRING),
            'password': openapi.Schema(type=openapi.TYPE_STRING),
        },
))
@api_view(['POST'])
def login(request):
    info = request.data.get('info')
    password = request.data.get('password')
    if info and password:
        try:
            if '@' in info:
                utente = User.objects.get(email = info)
            else:
                utente = User.objects.get(username = info)
            logging.info(password)
            logging.info(utente.password)
            login = bcrypt.checkpw(password.encode(), utente.password.encode())
            logging.info(login)
            if login :
                token, created = Token.objects.get_or_create(user=utente)
                logging.info(token.key)
                return Response(data={'token':token.key},status=status.HTTP_202_ACCEPTED)
            else:
                return Response({'error': 'Login failed, wrong credentials.'}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logging.error("Exception:"+str(e))
            return Response({'error': 'Login failed.'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error': 'Please provide username or email and password'}, status=status.HTTP_400_BAD_REQUEST)



class PollViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows polls to be viewed or edited.
    """
    queryset = Poll.objects.all().order_by('-pub_date')
    serializer_class = PollSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [PollsPermission]

    @swagger_auto_schema(request_body= openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'scelte' : openapi.Schema(type=openapi.TYPE_ARRAY, items = openapi.Schema(type=openapi.TYPE_STRING))
        }
    ))
    @action(methods = ["post"], detail = True)
    def choices(self, request, pk):
        poll = self.get_object()
        for choice in request.data['scelte']:
            Choice.objects.create(poll = poll, choice_text=choice)
        return Response({'success' : 'Scelte inserite correttamente'},status=status.HTTP_201_CREATED)
    @swagger_auto_schema(request_body= openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'choice_id' : openapi.Schema(type=openapi.TYPE_INTEGER, description="Id scelta votata"),
        }
    ))
    @action(methods = ["post"], detail = True)
    def vote(self, request, pk):
        poll = self.get_object()
        token = request.META.get('HTTP_AUTHORIZATION').split(" ")[1]
        user = Token.objects.get(key=token).user
        if poll.users.filter(username = user.username).exists(): 
            return Response({'info' : 'L\'utente ha già votato'},status=status.HTTP_302_FOUND)
        else:
            choice = Choice.objects.get(id = request.data['choice_id'])
            choice.votes += 1
            choice.save()
            poll.users.add(user)
            return Response({'success' : 'Sondaggio inserito correttamente'},status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        super_data = super().list(request, *args, **kwargs).data
        for i in super_data['results']:
            i.pop('users')
            i.pop('owner')
        return Response(super_data)
    @swagger_auto_schema(request_body= openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'question_text' : openapi.Schema(type=openapi.TYPE_STRING, description="Testo del sondaggio"),
            'pub_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Data pubblicazione"),
            'users': openapi.Schema(type=openapi.TYPE_ARRAY, items = openapi.Schema(type=openapi.TYPE_STRING))
        }
    ))
    def create(self, request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION').split(" ")[1]
        owner = Token.objects.get(key=token).user
        logging.info(owner)
        request.data['owner'] = owner
        usernames = request.data.pop('users', [])
        #request.data['owner'] = User.objects.get(username = request.data['owner'])
        poll = Poll.objects.create(**request.data)
        users = []
        for username in usernames:
            logging.info(users)
            users.append(User.objects.get(username = username))
            logging.info(users)
        poll.users.set(users)
        return Response({'success' : 'Sondaggio inserito correttamente'},status=status.HTTP_201_CREATED)  
    def retrieve(self, request, *args, **kwargs):
        super_data = super().retrieve(request, *args, **kwargs).data
        poll = self.get_object()
        choices = Choice.objects.filter(poll = poll)
        scelte = []
        for choice in choices:
            serializer = ChoiceSerializer(choice, context={'request':request})
            scelte.append({
                'url': serializer.data['url'],
                'Testo': choice.choice_text,
                'Voti': serializer.data['votes'],
            })
        choices_data = {
            'id sondaggio' : PollSerializer(poll, context={'request':request}).data['url'][-2],
            'owner' : super_data['owner'],
            'question_text': super_data['question_text'],
            'pub_date': super_data['pub_date'],
            'scelte' : scelte,
            'users' : [i.split('/', -1)[-2] for i in super_data['users']]
        }
        return Response(choices_data) 
    def update(self, request, pk=None):
        poll = self.get_object()
        usernames = request.data.get('users', [])
        request.data['users'] = []
        for username in usernames:
            request.data['users'].append(reverse('user-detail', args=[username]))
        serializer = PollSerializer(poll, data=request.data, context = {'request': request})
        if serializer.is_valid():
            serializer.update(poll, serializer.validated_data)
            return Response({'success' : 'Sondaggio modificato'},status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status = 400)   
    def partial_update(self, request, *args, **kwargs):
        poll = self.get_object()
        request_users = request.data.get('users')
        if request_users is not None:
            request.data['users'] = []
            for username in request_users:
                request.data['users'].append(reverse('user-detail', args=[username]))
        serializer = PollSerializer(poll, data=request.data, context = {'request': request}, partial=True)
        if serializer.is_valid():
            serializer.partial_update(poll, serializer.validated_data)
            return Response({'success' : 'Sondaggio modificato'},status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status = 400)   

class ChoiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows choices to be viewed or edited.
    """
    queryset = Choice.objects.all()
    serializer_class = ChoiceSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [ChoicePermission]

    @swagger_auto_schema(request_body= openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'poll' : openapi.Schema(type=openapi.TYPE_INTEGER),
            'choice_text': openapi.Schema(type=openapi.TYPE_STRING),
            'votes' : openapi.Schema(type=openapi.TYPE_INTEGER)
        }
    ))
    def create(self, request, *args, **kwargs):
        poll = request.data.get('poll')
        request.data['poll'] = reverse('poll-detail', args=[poll])
        serializer = ChoiceSerializer(data=request.data, context = {'request': request})
        if serializer.is_valid():
            serializer.create(serializer.validated_data)
            return Response({'success' : 'Scelta creata'},status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status = 400) 
    @swagger_auto_schema(operation_description=
                        "Restituisce:\n"+
                        "id - url della scelta\n"+
                        "poll - url del sondaggio di appartenenza\n"+
                        "choice_text - testo della scelta\n"+
                        "voti - numero di voti")
    def retrieve(self, request, *args, **kwargs):
        """Restituisce:\n
        url - url della scelta\n
        poll - url del sondaggio di appartenenza\n
        choice_text - testo della scelta\n
        voti - numero di voti"""
        
        return Response(super().retrieve(request, *args, **kwargs).data)

    @swagger_auto_schema(request_body= openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'poll' : openapi.Schema(type=openapi.TYPE_INTEGER, description="Id sondaggio di appartenenza"),
            'choice_text': openapi.Schema(type=openapi.TYPE_STRING, description="Testo della scelta"),
            'votes': openapi.Schema(type=openapi.TYPE_INTEGER, description="Numero di voti"),
        }
    ))
    def update(self, request, *args, **kwargs):
        choice = self.get_object()
        request.data['poll'] = reverse('poll-detail', args=[request.data['poll']])
        serializer = ChoiceSerializer(choice, data=request.data, context = {'request': request})
        if serializer.is_valid():
            serializer.update(choice, serializer.validated_data)
            return Response(serializer.data)
        return Response(serializer.errors, status = 400)
    
    @swagger_auto_schema(request_body= openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'poll' : openapi.Schema(type=openapi.TYPE_INTEGER, description="Id sondaggio di appartenenza"),
            'choice_text': openapi.Schema(type=openapi.TYPE_STRING, description="Testo della scelta"),
            'votes': openapi.Schema(type=openapi.TYPE_INTEGER, description="Numero di voti"),
        }
    ))
    def partial_update(self, request, *args, **kwargs):
        choice = self.get_object()
        if 'poll' in request.data:
            request.data['poll'] = reverse('poll-detail', args=[request.data['poll']])
        serializer = ChoiceSerializer(choice, data=request.data, context = {'request': request}, partial=True)
        if serializer.is_valid():
            serializer.partial_update(choice, serializer.validated_data)
            return Response(serializer.data)
        return Response(serializer.errors, status = 400)
    


    
    


