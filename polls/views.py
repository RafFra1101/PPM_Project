
from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from django.urls import reverse, get_resolver
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login
import requests, logging

url_api = "http://127.0.0.1:8000"
url_base = "http://127.0.0.1:8000"
logging.getLogger().setLevel(logging.INFO)
# Create your views here.
class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_poll_list"

    def get_queryset(self, **kwargs):
        """Return the last five published polls (not including those set to be published in the future)."""
        response = requests.get(url_api+reverse('poll-list'))
        data = response.json()
        output = []
        for x in data:
            output.append({
                'id' : x['url'].split('/', -1)[-2],
                'question_text': x['question_text'],
            })
        return output
    

def getChoices(self):
    """Return the choices of the poll"""
    url = url_api+reverse('poll-detail', args=[self.kwargs['poll_id']])
    response = requests.get(url)
    data = response.json()
    if 'detail' in self.template_name:
        
        if not self.request.session.get('username'):
            return{'voted':True, 'id': data['url'][-2]}
        if data['users'] and self.request.session['username'] in data['users']:
            messages.info(self.request, "L'utente ha già votato")
            return{'voted':True, 'id': data['url'].split('/', -1)[-2]}
    output = []
    info = {
        "id"    : data['url'].split('/', -1)[-2],
        "testo" : data['question_text'],
    }
    data = data['choices']
    scelte = []
    for choice in data:
        scelte.append({
            'id' : choice['url'].split('/', -1)[-2],
            'testo' : choice['choice_text'],
            'voti' : choice['votes']
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
    choice_id = request.POST.get('choice')
    url = url_api + reverse('choice-vote', args=[choice_id])
    if 'token' in request.session:
        headers = {"Authorization": "Token "+request.session['token']}
    """else:
        headers = """""
    response = requests.post(url=url, headers=headers)
    if response.status_code == 201:
        return HttpResponseRedirect(reverse("results", args=(poll_id,)))
    else:
        messages.info(request, response.json().get('info'))
        return HttpResponseRedirect(reverse("results", args=(poll_id,)))



class RegisterLoginView(generic.FormView):
    def form_valid(self, form):
        out = form.formMethod(self.request.session)
        if 'error' in out:
            messages.info(self.request, str(out['error']))
            if 'login' in self.template_name:
                return redirect(reverse('login'))
            else:
                return redirect(reverse('register'))
            
        return super().form_valid(form)
    
    def get_success_url(self):
        redirect_url = self.request.GET.get('next')
        if redirect_url:
            return redirect_url
        else:
            return reverse('index')

    

class ProfileView(generic.ListView):
    template_name = "polls/profile.html"
    context_object_name = "profile_data"

    def get_queryset(self, **kwargs):
        """Return user profile details"""
        try: 
           return {
                'username' : self.request.session['username'],
                'email' : self.request.session['email']
            }
        except:
            return []
    
    def logout(request):
        if 'token' in request.session:
            del request.session['token']
            del request.session['username']
            del request.session['email']
        redirect_url = request.GET.get('next')
        if redirect_url:
            return HttpResponseRedirect(redirect_url) 
        else:
            return HttpResponseRedirect(reverse("index"))
        
class VotedPollsView(generic.ListView):
    template_name = "polls/votedPolls.html"
    context_object_name = "polls"

    def get_queryset(self, **kwargs):
        """Return the last five published polls (not including those set to be published in the future)."""
        output = []
        username = str(self.request.session.get('username'))
        if username:
            url = url_api+reverse('user-votedPolls', args=[username])
            response = requests.get(url)
            data = response.json()
            for x in data:
                output.append({
                    'id' : x['url'].split('/', -1)[-2],
                    'question_text': x['question_text'],
                })
        return output
    
class OwnPollsView(generic.ListView):
    template_name = "polls/ownPolls.html"
    context_object_name = "polls"

    def get_queryset(self, **kwargs):
        """Return the last five published polls (not including those set to be published in the future)."""
        output = []
        username = str(self.request.session.get('username'))
        if username:
            url = url_api+reverse('user-ownPolls', args=[username])
            response = requests.get(url)
            data = response.json()
            for x in data:
                output.append({
                    'id' : x['url'].split('/', -1)[-2],
                    'question_text': x['question_text'],
                })
        return output
    
    def deletePoll(request, poll_id):
        url = url_api + reverse('poll-detail', args=[poll_id])
        if 'token' in request.session:
            headers = {"Authorization": "Token "+request.session['token']}
        response = requests.delete(url=url, headers=headers)
        if response.status_code == 200:
            messages.info(request, 'Sondaggio "'+response.json()['question_text']+'" correttamente eliminato')
            return HttpResponseRedirect(reverse("ownPolls"))
        else:
            messages.error(request, 'C\'è stato un problema')
            return HttpResponseRedirect(reverse("ownPolls"))
        