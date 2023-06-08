

# Create your views here.
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, renderers, permissions, authentication, status, mixins
from pollsAPI.serializers import *
from .models import Poll, Choice
from .permissions import PollsPermission
from django.http import JsonResponse
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth.hashers import Argon2PasswordHasher, make_password, check_password
import logging, requests

logging.getLogger().setLevel(logging.INFO)
api_url = "http://127.0.0.1:8000/"
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

@api_view(['GET'])
def userInfo(request, info):
    if '@' in info:
        utente = User.objects.get(email = info)
    else:
        utente = User.objects.get(username = info)
    return JsonResponse(UserSerializer(utente, context={'request':request}).data)
    


@swagger_auto_schema(method='post', request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['username', 'email', 'password'],
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING),
            'email': openapi.Schema(type=openapi.TYPE_STRING),
            'password': openapi.Schema(type=openapi.TYPE_STRING),
        },
))
@api_view(['POST'])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    if username and password and email:
        try:
            user = User.objects.create_user(username=username, password=make_password(password), email=email)
            token = Token.objects.create(user=user)
            logging.info(token.key)
            return Response(data={'token':token.key},status=status.HTTP_201_CREATED)
        except:
            return Response({'error': 'Registration failed.'}, status=status.HTTP_400_BAD_REQUEST)
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
            if login:
                token, created = Token.objects.get_or_create(user=utente)
                logging.info(token.key)
                return Response(data={'token':token.key},status=status.HTTP_202_ACCEPTED)
            else:
                return Response({'error': 'Login failed, wrong credentials.'}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logging.error(str(e))
            return Response({'error': 'Login failed.'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error': 'Please provide username or email and password'}, status=status.HTTP_400_BAD_REQUEST)

"""class GroupViewSet(viewsets.ModelViewSet):

    API endpoint that allows groups to be viewed or edited.

    queryset = Group.objects.all()
    serializer_class = GroupSerializer"""




class PollViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows polls to be viewed or edited.
    """
    queryset = Poll.objects.all().order_by('-pub_date')
    serializer_class = PollSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [PollsPermission]

    """choice_schema =openapi.Schema(type=openapi.TYPE_OBJECT, properties={
        'testo' : openapi.Schema(type=openapi.TYPE_STRING), 
    }, required=['testo'])"""
    @swagger_auto_schema(method='post', request_body= openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'scelte' : openapi.Schema(type=openapi.TYPE_ARRAY, items = openapi.Schema(type=openapi.TYPE_STRING))
        }
    ))
    @action(detail=True, methods=['get', 'post'])
    def choices(self, request, pk=None):
        """
        Returns a list of all the choices of the given poll
        """
        poll = self.get_object()
        choices = Choice.objects.filter(poll = poll)
        url_poll = PollSerializer(poll, context={'request':request}).data['url']
        if request.method == 'GET':       
            scelte = []
            for choice in choices:
                serializer = ChoiceSerializer(choice, context={'request':request})
                scelte.append({
                    'URL': serializer.data['url'],
                    'Testo': choice.choice_text,
                    'Voti': serializer.data['votes'],
                })
            choices_data = {
                'URL sondaggio' : url_poll,
                'scelte' : scelte
            }
            return Response(choices_data)
        else:
            for choice in request.data['scelte']:
                Choice.objects.create(poll = poll, choice_text=choice)
            return Response({'success' : 'Scelte inserite correttamente'},status=status.HTTP_201_CREATED)
        

class ChoiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows choices to be viewed or edited.
    """
    queryset = Choice.objects.all()
    serializer_class = ChoiceSerializer
    @swagger_auto_schema(operation_description=
                        "Restituisce:\n"+
                        "id - id della scelta\n"+
                        "poll - id del sondaggio di appartenenza\n"+
                        "choice_text - testo della scelta\n"+
                        "voti - numero di voti")
    def retrieve(self, request, *args, **kwargs):
        """
            Restituisce:
                id - id della scelta
                poll - id del sondaggio di appartenenza
                choice_text - testo della scelta
                voti - numero di voti
        """
        data = super().retrieve(request, *args, **kwargs).data
        output = {
            "id" : data['url'][-2],
            "poll": data['poll'][-2],
            "choice_text": data['choice_text'],
            "voti": data['votes']
        }
        return Response(output)

    @swagger_auto_schema(request_body= openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'poll' : openapi.Schema(type=openapi.TYPE_INTEGER, description="Id sondaggio di appartenenza"),
            'testo': openapi.Schema(type=openapi.TYPE_STRING, description="Testo della scelta"),
            'users': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), description="Lista username degli utenti che hanno votato")
        }
    ))
    def update(self, request, *args, **kwargs):
        choice = self.get_object()
        logging.info(choice)
        pollSerializer = PollSerializer(data={'url': reverse('poll-detail', args=[request.data['poll']])})
        if pollSerializer.is_valid():
            choice.poll = pollSerializer.validated_data['url']     
        choice.choice_text = request.data['testo']
        usernames = request.data.get('users', [])
        users = User.objects.filter(username__in = usernames)
        logging.info(users)
        choice.users.set(users)
        choice.save()
        return Response({'success' : 'Prova funzionante'},status=status.HTTP_201_CREATED)
    
    


class PollDetailView(APIView):
    """
    View to list poll details.

    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PollSerializer

    model = Poll

    def get_queryset(self):
        """
        Excludes any polls that aren't published yet.
        """
        return Poll.objects.filter(pub_date__lte=timezone.now())
    
    



