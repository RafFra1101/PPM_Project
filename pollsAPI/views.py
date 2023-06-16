
# Create your views here.
from django.contrib.auth.models import User
from rest_framework import viewsets, status, mixins
from pollsAPI.serializers import *
from .models import Poll, Choice
from .permissions import PollsPermission, ChoicePermission, UsersPermission
from django.utils.decorators import method_decorator
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from drf_yasg import openapi as oa
from drf_yasg.utils import swagger_auto_schema
from django.urls import reverse
import bcrypt


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
    authentication_classes = [TokenAuthentication]
    permission_classes = [ChoicePermission]

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
                                'votes' : oa.Schema(type=oa.TYPE_INTEGER, description="numero di voti", default=0),
                                'users': oa.Schema(type=oa.TYPE_ARRAY, items = oa.Schema(type=oa.TYPE_STRING), description="username degli utenti che hanno già votato")
                            }, required=['poll', 'choice_text']
        ), responses={201: "Scelta creata\nid: id della scelta\nmissingUsers : username non esistenti (chiave mancante in caso di inserimento di tutti gli utenti)", 400: "Errore serializer"})
    def create(self, request, *args, **kwargs):
        poll = request.data.get('poll')
        request.data['poll'] = reverse('poll-detail', args=[poll])
        usernames = request.data.get('users', [])
        users = []
        missingUsers= []
        out = {'success' : 'Scelta creata', 'id': choice.id}
        for username in usernames:
            try:
                users.append(User.objects.get(username = username))
            except User.DoesNotExist:
                missingUsers.append(username)
        if len(missingUsers) > 0:
            out['missingUsers'] = missingUsers
        if not request.data.get('votes') or request.data['votes']<0: 
            request.data['votes'] = 0
        serializer = ChoiceSerializer(data=request.data, context = {'request': request})
        if serializer.is_valid():
            choice = serializer.create(serializer.validated_data)
            choice.users.set(users)
            return Response(out,status=status.HTTP_201_CREATED)
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

    @swagger_auto_schema(operation_description=ChoicePermission.get_permission_string('vote')+"\nPermette di votare una scelta di un sondaggio",
                         responses={201:"success : Voto inserito correttamente", 302: "L\'utente ha già votato"})
    @action(methods = ["get"], detail = True)
    def vote(self, request, pk):
        choice = self.get_object()
        poll = choice.poll
        user = request.user
        if choice.users.filter(username = user.username).exists():         
            return Response({'info' : 'L\'utente ha già votato'},status=status.HTTP_302_FOUND)
        else:
            choice.votes += 1
            choice.users.add(user)
            choice.save()
            return Response({'success' : 'Voto inserito correttamente'},status=status.HTTP_201_CREATED)

@swagger_auto_schema(method='post', responses={202: "token : stringa_token\nusername : username\nemail : email", 
                                               400: "error : Login failed, wrong password", 
                                               404: "error : Login failed, user does not exist",
                                               500: "Exception: messaggio eccezione"},
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
                return Response(data={'token':token.key, 'username': utente.username, 'email' : utente.email},status=status.HTTP_202_ACCEPTED)
            else:
                return Response({'error': 'Login failed, wrong password'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'Login failed, user does not exist'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'Exception': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
            i.pop('owner')
        return Response(super_data['results'])
    @swagger_auto_schema(operation_description=PollsPermission.get_permission_string('create'), request_body= oa.Schema(
        type=oa.TYPE_OBJECT,
        properties={
            'question_text' : oa.Schema(type=oa.TYPE_STRING, description="Testo del sondaggio"),
            'pub_date': oa.Schema(type=oa.TYPE_STRING, format=oa.FORMAT_DATETIME, description="Data pubblicazione")
        }, required=['question_text', "pub_date"]
    ), responses={201: 'success : Sondaggio inserito correttamente\nid : id del sondaggio'})
    def create(self, request, *args, **kwargs):
        owner = request.user
        poll = Poll.objects.create(question_text=request.data['question_text'], pub_date=request.data['pub_date'], owner = owner)  
        return Response({'success' : 'Sondaggio inserito correttamente', 'id': poll.id} ,status=status.HTTP_201_CREATED)  
    @swagger_auto_schema(operation_description=PollsPermission.get_permission_string('retrieve'),
                         responses={200: oa.Response('Schema valori di ritorno' , oa.Schema(type=oa.TYPE_OBJECT, properties={
                            'url' : oa.Schema(type=oa.TYPE_INTEGER, description="url sondaggio"),
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
        users = []
        for choice in choices:
            serializer = ChoiceSerializer(choice, context={'request':request})
            scelte.append({
                'url': serializer.data['url'],
                'choice_text': choice.choice_text,
                'votes': serializer.data['votes'],
            })
            if len(serializer.data['users']) > 0:
                users.extend([i.split('/', -1)[-2] for i in serializer.data['users']])
            
        choices_data = {
            'url' : PollSerializer(poll, context={'request':request}).data['url'],
            'owner' : super_data['owner'],
            'question_text': super_data['question_text'],
            'pub_date': super_data['pub_date'],
            'choices' : scelte,
            'users' : users
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
    @swagger_auto_schema(operation_description=PollsPermission.get_permission_string('destroy'),
        responses={200: 'question_text : testo del sondaggio',
                  400: 'error : C\'è stato un problema'})
    def destroy(self, request, *args, **kwargs):
        testo = self.get_object().question_text
        if super().destroy(request, *args, **kwargs).status_code == 204:
            return Response({'question_text' : testo} ,status=status.HTTP_200_OK)
        else:
            return Response({'error' : "C'è stato un problema"} ,status=status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(operation_description=PollsPermission.get_permission_string('choices')+"\nPermette di inserire nuove scelte ad un sondaggio", request_body= oa.Schema(
        type=oa.TYPE_OBJECT,
        properties={
            'choices' : oa.Schema(type=oa.TYPE_ARRAY, items = oa.Schema(type=oa.TYPE_OBJECT, properties={
                'choice_text' : oa.Schema(type=oa.TYPE_STRING),
                'votes' : oa.Schema(type=oa.TYPE_INTEGER),
                'users': oa.Schema(type=oa.TYPE_ARRAY, items = oa.Schema(type=oa.TYPE_STRING), description="username degli utenti che hanno già votato")
            }, required=['scelte']))
        }
    ), responses={201: "success : Scelte inserite correttamente"})
    @action(methods = ["post"], detail = True)
    def choices(self, request, pk):
        poll = self.get_object()
        oldChoices = list(Choice.objects.filter(poll = poll))
        newChoices = request.data['choices']
        if len(newChoices) == 0:
            for choice in oldChoices:
                choice.delete()
        elif len(oldChoices) == 0:
            for choice in newChoices:
                if choice['votes'] < 0: choice['votes'] = 0
                choice = Choice.objects.create(poll = poll, choice_text=choice['choice_text'], votes=choice['votes'])
        else:
            i = 0
            for i in range(i, min(len(oldChoices), len(newChoices))):
                oldChoices[i].choice_text = newChoices[i]['choice_text']
                oldChoices[i].votes = newChoices[i]['votes'] if newChoices[i]['votes'] >= 0 else 0
                oldChoices[i].save()
            i += 1
            for x in range(i, len(oldChoices)):
                oldChoices[x].delete()
            for x in range(i, len(newChoices)):
                Choice.objects.create(poll = poll, choice_text=newChoices[x]['choice_text'], votes=newChoices[x]['votes'] if newChoices[x]['votes'] >= 0 else 0)
        return Response({'success' : 'Scelte inserite correttamente'},status=status.HTTP_201_CREATED)


@swagger_auto_schema(method='post', responses={201: "token : stringa_token\nusername : username\nemail : email", 
                                               400: "error : Please provide username, password and email.\nemail : Questa email è già stata utilizzata\nusername : Questo username è già stato utilizzato", 
                                               500: "Exception: messaggio eccezione"},
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
                token = Token.objects.create(user=user)
                return Response(data={'token':token.key, 'username': user.username, 'email' : user.email},status=status.HTTP_201_CREATED)
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
        










    


    
    



