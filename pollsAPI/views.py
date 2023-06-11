
# Create your views here.
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, renderers, permissions, authentication, status, mixins
from pollsAPI.serializers import *
from .models import Poll, Choice
from .permissions import PollsPermission, ChoicePermission, UsersPermission
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from drf_yasg import openapi as oa
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth.hashers import Argon2PasswordHasher, make_password, check_password
import logging, requests, bcrypt

logging.getLogger().setLevel(logging.INFO)
token_needed = "È necessario passare un token nell'header come 'Authorization: Token stringa_token'"
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_description=ChoicePermission.get_permission_string('retrieve')
))
@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_description=ChoicePermission.get_permission_string('destroy')
))
class ChoiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows choices to be viewed or edited.
    """
    queryset = Choice.objects.all()
    serializer_class = ChoiceSerializer
    """authentication_classes = [TokenAuthentication]
    permission_classes = [ChoicePermission]"""

    @swagger_auto_schema(operation_description=ChoicePermission.get_permission_string('list'),
                         responses={200: oa.Response('Schema valori di ritorno', oa.Schema(type=oa.TYPE_ARRAY, 
                                                                        items=oa.Schema(type=oa.TYPE_OBJECT,
                                                                                     properties={
                                                                                        'url' : oa.Schema(type=oa.TYPE_STRING, description="url scelta"),
                                                                                        'poll' : oa.Schema(type=oa.TYPE_INTEGER, description="id del sondaggio a cui appartiene la scelta"),
                                                                                        'choice_text': oa.Schema(type=oa.TYPE_STRING,description="testo della scelta"),
                                                                                        'votes' : oa.Schema(type=oa.TYPE_INTEGER, description="numero di voti")
                                                                                     })))})
    def list(self, request, *args, **kwargs):
        return Response(super().list(request, *args, **kwargs).data['results'])
    @swagger_auto_schema(operation_description=ChoicePermission.get_permission_string('create'),
                         request_body= oa.Schema(
                            type=oa.TYPE_OBJECT,
                            properties={
                                'poll' : oa.Schema(type=oa.TYPE_INTEGER, description="id del sondaggio a cui appartiene la scelta"),
                                'choice_text': oa.Schema(type=oa.TYPE_STRING,description="testo della scelta"),
                                'votes' : oa.Schema(type=oa.TYPE_INTEGER, description="numero di voti", default=0)
                            }, required=['poll', 'choice_text']
        ), responses={201: "Scelta creata\nid: id della scelta", 400: "Errore serializer"})
    def create(self, request, *args, **kwargs):
        poll = request.data.get('poll')
        request.data['poll'] = reverse('poll-detail', args=[poll])
        if not request.data.get('votes'): request.data['votes'] = 0
        serializer = ChoiceSerializer(data=request.data, context = {'request': request})
        if serializer.is_valid():
            choice = serializer.create(serializer.validated_data)
            return Response({'success' : 'Scelta creata', 'id': choice.id},status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status = 400) 

    @swagger_auto_schema(operation_description = ChoicePermission.get_permission_string('update'),
                         responses={200: ChoiceSerializer, 400: "Errore serializer"},
                         request_body= oa.Schema(
        type=oa.TYPE_OBJECT,
        properties={
            'poll' : oa.Schema(type=oa.TYPE_INTEGER, description="Id sondaggio di appartenenza"),
            'choice_text': oa.Schema(type=oa.TYPE_STRING, description="Testo della scelta"),
            'votes': oa.Schema(type=oa.TYPE_INTEGER, description="Numero di voti"),
        }, required=['poll', 'choice_text', 'votes']
    ))
    def update(self, request, *args, **kwargs):
        choice = self.get_object()
        request.data['poll'] = reverse('poll-detail', args=[request.data['poll']])
        serializer = ChoiceSerializer(choice, data=request.data, context = {'request': request})
        if serializer.is_valid():
            serializer.update(choice, serializer.validated_data)
            return Response(serializer.data)
        return Response(serializer.errors, status = 400)
    
    @swagger_auto_schema(operation_description = ChoicePermission.get_permission_string('partial_update'), request_body= oa.Schema(
        type=oa.TYPE_OBJECT,
        properties={
            'poll' : oa.Schema(type=oa.TYPE_INTEGER, description="Id sondaggio di appartenenza"),
            'choice_text': oa.Schema(type=oa.TYPE_STRING, description="Testo della scelta"),
            'votes': oa.Schema(type=oa.TYPE_INTEGER, description="Numero di voti"),
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

    @swagger_auto_schema(operation_description=PollsPermission.get_permission_string('vote')+"\nPermette di votare una scelta di un sondaggio\n"+token_needed,
                         request_body=oa.Schema(type=oa.TYPE_OBJECT, properties={}, description="Nessun parametro necessario"))
    @action(methods = ["post"], detail = True)
    def vote(self, request, pk):
        choice = self.get_object()
        poll = choice.poll
        token = request.META.get('HTTP_AUTHORIZATION').split(" ")[1]
        user = Token.objects.get(key=token).user
        if poll.users.filter(username = user.username).exists(): 
            return Response({'info' : 'L\'utente ha già votato'},status=status.HTTP_302_FOUND)
        else:
            choice.votes += 1
            choice.save()
            poll.users.add(user)
            poll.save()
            return Response({'success' : 'Voto inserito correttamente'},status=status.HTTP_201_CREATED)

@swagger_auto_schema(method='post', responses={202: "token : stringa_token", 400: "error : Login failed, wrong credentials", 500: "Exception: messaggio eccezione"},
                     request_body=oa.Schema(
        type=oa.TYPE_OBJECT,
        required=['info', 'password'],
        properties={
            'info': oa.Schema(type=oa.TYPE_STRING, description="Username o email dell'utente"),
            'password': oa.Schema(type=oa.TYPE_STRING),
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
            login = bcrypt.checkpw(password.encode(), utente.password.encode())
            if login :
                token, created = Token.objects.get_or_create(user=utente)
                logging.info("Token: "+token.key)
                return Response(data={'token':token.key},status=status.HTTP_202_ACCEPTED)
            else:
                return Response({'error': 'Login failed, wrong credentials'}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({'Exception': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({'error': 'Please provide username or email and password'}, status=status.HTTP_400_BAD_REQUEST)
    
@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_description=PollsPermission.get_permission_string('destroy')
))
class PollViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows polls to be viewed or edited.
    """
    queryset = Poll.objects.all().order_by('-pub_date')
    serializer_class = PollSerializer
    """authentication_classes = [TokenAuthentication]
    permission_classes = [PollsPermission]"""

    @swagger_auto_schema(operation_description=PollsPermission.get_permission_string('list'),
                         responses={200: oa.Response('Schema valori di ritorno', oa.Schema(type=oa.TYPE_ARRAY, 
                                                                        items=oa.Schema(type=oa.TYPE_OBJECT,
                                                                                     properties={
                                                                                        'url' : oa.Schema(type=oa.TYPE_STRING, description="url sondaggio"),
                                                                                        'question_text': oa.Schema(type=oa.TYPE_STRING,description="testo del sondaggio"),
                                                                                        'pub_date' : oa.Schema(type=oa.TYPE_STRING, format=oa.FORMAT_DATETIME, description="data di pubblicazione")
                                                                                     })))})
    def list(self, request, *args, **kwargs):
        super_data = super().list(request, *args, **kwargs).data
        for i in super_data['results']:
            i.pop('users')
            i.pop('owner')
        return Response(super_data['results'])
    @swagger_auto_schema(operation_description=PollsPermission.get_permission_string('create')+"\ntoken_needed", request_body= oa.Schema(
        type=oa.TYPE_OBJECT,
        properties={
            'question_text' : oa.Schema(type=oa.TYPE_STRING, description="Testo del sondaggio"),
            'pub_date': oa.Schema(type=oa.TYPE_STRING, format=oa.FORMAT_DATETIME, description="Data pubblicazione"),
            'users': oa.Schema(type=oa.TYPE_ARRAY, items = oa.Schema(type=oa.TYPE_STRING), description="username degli utenti che hanno già votato")
        }, required=['question_text', "pub_date"]
    ), responses={201: 'success : Sondaggio inserito correttamente\nid : id del sondaggio\nmissingUsers : username non esistenti (chiave mancante in caso di inserimento di tutti gli utenti)'})
    def create(self, request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION').split(" ")[1]
        owner = Token.objects.get(key=token).user
        logging.info(owner)
        request.data['owner'] = owner
        usernames = request.data.pop('users', [])
        users = []
        missingUsers= []
        for username in usernames:
            try:
                users.append(User.objects.get(username = username))
            except User.DoesNotExist:
                missingUsers.append(username)
        poll = Poll.objects.create(**request.data)
        
        poll.users.set(users)
        out = {'success' : 'Sondaggio inserito correttamente', 'id': poll.id}
        if len(missingUsers) > 0:
            out['missingUsers'] = missingUsers
        return Response(out ,status=status.HTTP_201_CREATED)  
    @swagger_auto_schema(operation_description=PollsPermission.get_permission_string('retrieve'),
                         responses={200: oa.Response('Schema valori di ritorno' , oa.Schema(type=oa.TYPE_OBJECT, properties={
                            'id' : oa.Schema(type=oa.TYPE_INTEGER, description="id sondaggio"),
                            'owner': oa.Schema(type=oa.TYPE_STRING,description="username proprietario del sondaggio"),
                            'question_text': oa.Schema(type=oa.TYPE_STRING,description="testo del sondaggio"),
                            'pub_date' : oa.Schema(type=oa.TYPE_STRING, format=oa.FORMAT_DATETIME, description="data di pubblicazione"),                                                
                            'choices' : oa.Schema(type=oa.TYPE_ARRAY, items = oa.Schema(type=oa.TYPE_OBJECT,
                                properties={
                                'url' : oa.Schema(type=oa.TYPE_STRING, description="url scelta"),
                                'choice_text': oa.Schema(type=oa.TYPE_STRING,description="testo della scelta"),
                                'votes' : oa.Schema(type=oa.TYPE_INTEGER, description="numero di voti")
                                })),
                            'users' : oa.Schema(type=oa.TYPE_ARRAY, items = oa.Schema(type=oa.TYPE_STRING, description="username utente"))
                         }))})
    def retrieve(self, request, *args, **kwargs):
        super_data = super().retrieve(request, *args, **kwargs).data
        poll = self.get_object()
        choices = Choice.objects.filter(poll = poll)
        scelte = []
        for choice in choices:
            serializer = ChoiceSerializer(choice, context={'request':request})
            scelte.append({
                'url': serializer.data['url'],
                'choice_text': choice.choice_text,
                'votes': serializer.data['votes'],
            })
        choices_data = {
            'id' : PollSerializer(poll, context={'request':request}).data['url'][-2],
            'owner' : super_data['owner'],
            'question_text': super_data['question_text'],
            'pub_date': super_data['pub_date'],
            'choices' : scelte,
            'users' : [i.split('/', -1)[-2] for i in super_data['users']]
        }
        return Response(choices_data) 
    
    @swagger_auto_schema(operation_description=PollsPermission.get_permission_string('update'), request_body= oa.Schema(
        type=oa.TYPE_OBJECT,
        properties={
            'owner' : oa.Schema(type=oa.TYPE_STRING, description="username proprietario del sondaggio"),
            'question_text' : oa.Schema(type=oa.TYPE_STRING, description="Testo del sondaggio"),
            'pub_date': oa.Schema(type=oa.TYPE_STRING, format=oa.FORMAT_DATETIME, description="Data pubblicazione"),
            'users': oa.Schema(type=oa.TYPE_ARRAY, items = oa.Schema(type=oa.TYPE_STRING), description="username degli utenti che hanno già votato")
        }, required=['owner', 'question_text', "pub_date"]
    ), responses={202: 'success : Sondaggio modificato\nmissingUsers : username non esistenti (mancante in caso di inserimento di tutti gli utenti)',
                  400: 'Errore serializer',
                  404: 'Utente proprietario non esistente'})
    def update(self, request, pk=None):
        poll = self.get_object()
        if not User.objects.filter(username=request.data['owner']).exists():
            return Response({'error' : 'Utente proprietario non esistente'}, status=status.HTTP_404_NOT_FOUND)
        usernames = request.data.get('users', [])
        request.data['users'] = []
        missingUsers = []
        for username in usernames:
            if User.objects.filter(username=username).exists():
                request.data['users'].append(reverse('user-detail', args=[username]))
            else:
                missingUsers.append(username)
        serializer = PollSerializer(poll, data=request.data, context = {'request': request})
        if serializer.is_valid():
            serializer.update(poll, serializer.validated_data)
            out = {'success' : 'Sondaggio modificato'}
            if len(missingUsers) > 0:
                out['missingUsers'] = missingUsers
            return Response(out ,status=status.HTTP_202_ACCEPTED) 
        return Response(serializer.errors, status = 400) 
      
    @swagger_auto_schema(operation_description=PollsPermission.get_permission_string('partial_update'), request_body= oa.Schema(
        type=oa.TYPE_OBJECT,
        properties={
            'owner' : oa.Schema(type=oa.TYPE_STRING, description="username proprietario del sondaggio"),
            'question_text' : oa.Schema(type=oa.TYPE_STRING, description="Testo del sondaggio"),
            'pub_date': oa.Schema(type=oa.TYPE_STRING, format=oa.FORMAT_DATETIME, description="Data pubblicazione"),
            'users': oa.Schema(type=oa.TYPE_ARRAY, items = oa.Schema(type=oa.TYPE_STRING), description="username degli utenti che hanno già votato")
        }
    ), responses={202: 'success : Sondaggio modificato \nmissingUsers : username non esistenti (mancante in caso di inserimento di tutti gli utenti)',
                  400: 'Errore serializer',
                  404: 'Utente proprietario non esistente'})
    def partial_update(self, request, *args, **kwargs):
        poll = self.get_object()
        request_users = request.data.get('users')
        missingUsers = []
        if request_users is not None:
            request.data['users'] = []
            for username in request_users:
                if User.objects.filter(username=username).exists():
                    request.data['users'].append(reverse('user-detail', args=[username]))
                else:
                    missingUsers.append(username)
        serializer = PollSerializer(poll, data=request.data, context = {'request': request}, partial=True)
        if serializer.is_valid():
            serializer.partial_update(poll, serializer.validated_data)
            out = {'success' : 'Sondaggio modificato'}
            if len(missingUsers) > 0:
                out['missingUsers'] = missingUsers
            return Response(out ,status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status = 400)   
    
    @swagger_auto_schema(operation_description=PollsPermission.get_permission_string('choices')+"\nPermette di inserire nuove scelte ad un sondaggio", request_body= oa.Schema(
        type=oa.TYPE_OBJECT,
        properties={
            'scelte' : oa.Schema(type=oa.TYPE_ARRAY, items = oa.Schema(type=oa.TYPE_STRING))
        }
    ), responses={201: "success : Scelte inserite correttamente"})
    @action(methods = ["post"], detail = True)
    def choices(self, request, pk):
        poll = self.get_object()
        for choice in request.data['scelte']:
            Choice.objects.create(poll = poll, choice_text=choice)
        return Response({'success' : 'Scelte inserite correttamente'},status=status.HTTP_201_CREATED)


@swagger_auto_schema(method='post', responses={201: "token : stringa_token", 400: "error : Please provide username, password and email.", 500: "Exception: messaggio eccezione"},
                     request_body=oa.Schema(
        type=oa.TYPE_OBJECT,
        required=['username', 'email', 'password'],
        properties={
            'username': oa.Schema(type=oa.TYPE_STRING),
            'email': oa.Schema(type=oa.TYPE_STRING, format=oa.FORMAT_EMAIL),
            'password': oa.Schema(type=oa.TYPE_STRING, format=oa.FORMAT_PASSWORD),
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
            return Response({'Exception': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({'error': 'Please provide username, password and email.'}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_description=UsersPermission.get_permission_string('destroy')
))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(
    operation_description=UsersPermission.get_permission_string('retrieve')
))
class UserViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    
    """API endpoint that allows users to be viewed or edited."""
    
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    lookup_field = 'username'
    authentication_classes = [TokenAuthentication]
    permission_classes = [UsersPermission]

    @swagger_auto_schema(operation_description=UsersPermission.get_permission_string('list'),
                         responses={200: oa.Response('Schema valori di ritorno', oa.Schema(type=oa.TYPE_ARRAY, description="Lista degli utenti", 
                                                                        items=oa.Schema(type=oa.TYPE_OBJECT,
                                                                                     properties={
                                                                                        'url' : oa.Schema(type=oa.TYPE_STRING, description="url utente"),
                                                                                        'username' : oa.Schema(type=oa.TYPE_STRING, description="nome utente"),
                                                                                     })))})
    def list(self, request, *args, **kwargs):
        super_data = super().list(request, *args, **kwargs).data
        for i in super_data['results']:
            i.pop('password')
            i.pop('email')
        return Response(super_data['results'])
    
    @swagger_auto_schema(operation_description=UsersPermission.get_permission_string('ownPolls'),
                         responses={200: oa.Response('Schema valori di ritorno', PollSerializer(many=True))})
    @action(methods = ["get"], detail = True)
    def ownPolls(self, request, username=None):
        polls = Poll.objects.filter(owner = username)
        serializer = PollSerializer(polls, many=True, context={'request':request})
        return Response(serializer.data)
    
    @swagger_auto_schema(operation_description=UsersPermission.get_permission_string('votedPolls'),
                         responses={200: oa.Response('Schema valori di ritorno', PollSerializer(many=True))})
    @action(methods = ["get"], detail = True)
    def votedPolls(self, request, username=None):
        polls = Poll.objects.filter(users__username = username)
        serializer = PollSerializer(polls, many=True, context={'request':request})
        return Response(serializer.data)
        

    










    


    
    



