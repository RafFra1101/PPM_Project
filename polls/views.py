
from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from django.urls import reverse, get_resolver
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login
from .forms import RegisterForm, LoginForm
import requests, logging

# Create your views here.
class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_poll_list"

    def get_queryset(self):
        """Return the last five published polls (not including those set to be published in the future)."""
        response = requests.get('http://127.0.0.1:8000/api/polls/')  # Sostituisci l'URL con l'API reale che desideri chiamare
        data = response.json()  # Se la risposta è in formato JSON
        output = []
        #logging.error(data['results'][0]['url'][-2])
        for x in data['results']:
            output.append({
                'id': x['url'][-2],
                'question_text': x['question_text'],
            })
        # Puoi passare i dati recuperati dall'API al contesto della vista

        return output
    

def getChoices(self):
    """Return the choices of the poll"""
    response = requests.get('http://127.0.0.1:8000/api/polls/'+str(self.kwargs['poll_id'])+'/choices/')
    data = response.json()
    url = data['URL sondaggio']
    response = requests.get(url).json()
    #response = requests.get("http://127.0.0.1:8000/api/polls/1").json()
    output = []
    
    info = {
        "testo" : response['question_text'],
        "id"    : url[-2],
    }
    data = data['scelte']
    scelte = []
    for choice in data:
        scelte.append({
            'id' : choice['URL'][-2],
            'testo' : choice['Testo'],
            'voti' : choice['Voti']
        })

    output = {
        'info' :info,
        'scelte':scelte
    }
    return output

class PollView(generic.ListView):
    context_object_name = "data"
    get_queryset = getChoices

def vote(request, poll_id):
    choice = request.POST["choice"].split(" / ")
    response = requests.patch("http://127.0.0.1:8000/api/choice/"+choice[0]+"/", data={'votes': int(choice[1])+1})
    return HttpResponseRedirect(reverse("results", args=(poll_id,)))

class RegisterView(generic.FormView):
    template_name = "polls/register.html"
    form_class = RegisterForm
    success_url = "http://127.0.0.1:8000/login"
    def form_valid(self, form):
        out = form.register()
        if 'error' in out:
            messages.info(self.request, str(out['error']))
            return redirect("http://127.0.0.1:8000/register")
        return super().form_valid(form)
    
class LoginView(generic.FormView):
    template_name = "polls/login.html"
    form_class = LoginForm
    success_url = "http://127.0.0.1:8000/"

    def form_valid(self, form):
        out = form.login()
        logging.warning(out)
        if out:
            return super().form_valid(form)
        else:
            messages.info(self.request, "Credenziali errate")
            return redirect("http://127.0.0.1:8000/login")