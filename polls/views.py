
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.views import generic
from django.urls import reverse
from django.contrib import messages
from .forms import newPollForm, editPollForm
from datetime import datetime
import requests, logging

class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_poll_list"

    def get_queryset(self, **kwargs):
        """Return the last published polls"""
        response = requests.get(settings.URL+reverse('poll-list'))
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
    url = settings.URL+reverse('poll-detail', args=[self.kwargs['poll_id']])
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
    url = settings.URL + reverse('choice-vote', args=[choice_id])
    if 'token' in request.session:
        headers = {"Authorization": "Token "+request.session['token']}
    response = requests.get(url=url, headers=headers)
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
            if 'token' in self.request.session:
                headers = {"Authorization": "Token "+self.request.session['token']}
            url = settings.URL+reverse('user-votedPolls', args=[username])
            response = requests.get(url, headers=headers)
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
            url = settings.URL+reverse('user-ownPolls', args=[username])
            response = requests.get(url)
            data = response.json()
            for x in data:
                output.append({
                    'id' : x['url'].split('/', -1)[-2],
                    'question_text': x['question_text'],
                })
        return output
    
    def deletePoll(request, poll_id):
        url = settings.URL + reverse('poll-detail', args=[poll_id])
        if 'token' in request.session:
            headers = {"Authorization": "Token "+request.session['token']}
        response = requests.delete(url=url, headers=headers)
        if response.status_code == 200:
            messages.info(request, 'Sondaggio "'+response.json()['question_text']+'" correttamente eliminato')
            return HttpResponseRedirect(reverse("ownPolls"))
        else:
            messages.error(request, 'C\'è stato un problema')
            return HttpResponseRedirect(reverse("ownPolls"))
        
class newPollView(generic.FormView):
    form_class = newPollForm
    template_name="polls/newPoll.html"

    def form_valid(self, form):
        data = form.newPoll(self.request.session)
        choices = []
        if 'token' in self.request.session:
                headers = {"Authorization": "Token "+self.request.session['token']}
        for choice, start_votes in zip(self.request.POST.getlist('choice'), self.request.POST.getlist('votes')):
            if choice.strip() != "":
                if start_votes == "":
                    start_votes = 0
                choices.append({
                    'choice_text' : choice,
                    'votes' : start_votes
                })       
        request_data = {
            'question_text' : data['question_text'],
            'pub_date' : datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }
        out = requests.post(settings.URL+reverse('poll-list'), request_data, headers=headers)
        if out.status_code == 201:
            out = out.json()
            id = out['id']
            if len(choices) > 0:
                outChoices = requests.post(settings.URL+reverse('poll-choices', args=[id]), json={'choices' : choices}, headers=headers)
                if outChoices.status_code != 201:
                    messages.warning(self.request, "Scelte non aggiunte")
            if self.request.session['username'] != data['owner']:
                outOwner = requests.patch(settings.URL+reverse('poll-detail', args=[id]), {'owner' : data['owner']}, headers=headers)
                if outOwner.status_code >= 400:
                    messages.warning(self.request, "L'utente corrente è il proprietario")
            messages.info(self.request, "Sondaggio creato")
            return redirect(reverse('ownPolls'))
        else:
            messages.error(self.request, "Sondaggio non creato")
            return redirect(reverse('newPoll'))

def editPoll(request, poll_id):
    out = requests.get(settings.URL+reverse('poll-detail', args=[poll_id]))
    choices = []
    if out.status_code != 200:
        context = {}
    else:
        out = out.json()
        for choice in out['choices']:
            choices.append({
                'choice_text' : choice['choice_text'],
                'votes' : choice['votes']
            })
        initial_dict = {
            'question_text' : out['question_text'],
            'owner' : out['owner'],
            'choices' : choices
        }

        if request.method == 'POST':
            data = request.POST
            choices = []
            if 'token' in request.session:
                headers = {"Authorization": "Token "+request.session['token']}
            for key, value in data.items():
                if key.startswith('choice_text'):
                    index = key.replace('choice_text', '')
                    vote_key = 'votes' + index
                    if vote_key in data:
                        choice_dict = {
                            'choice_text': value,
                            'votes': int(data[vote_key]) if data[vote_key]!="" else 0
                        }
                        choices.append(choice_dict)
            request_data = {}
            if data['question_text'] != initial_dict['question_text']:
                request_data['question_text'] = data['question_text']
            if data['owner'] != initial_dict['owner']:
                request_data['owner'] = data['owner']
            out = requests.patch(settings.URL+reverse('poll-detail', args=[poll_id]), data=request_data, headers=headers)
            if choices != initial_dict['choices']:
                out = requests.post(settings.URL+reverse('poll-choices', args=[poll_id]), json={'choices' : choices}, headers=headers)
            return redirect(reverse('ownPolls'))
        else:
            form = editPollForm(data = initial_dict)
        
        context = {'form': form}
    return render(request, 'polls/editPoll.html', context)
        

        