
from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.views import generic
from django.urls import reverse
from django.utils import timezone
import requests, logging

# Create your views here.
class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """Return the last five published questions (not including those set to be published in the future)."""
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
    

class PollView(generic.ListView):
    template_name = "polls/detail.html"
    context_object_name = "choices"

    def get_queryset(self):
        """Return the choices of the poll"""
        url = 'http://127.0.0.1:8000/api/polls/'+str(self.kwargs['question_id'])+'/choices/'
        response = requests.get(url)  # Sostituisci l'URL con l'API reale che desideri chiamare
        data = response.json()  # Se la risposta è in formato JSON
        response = requests.get(data[0]['URL sondaggio'])
        
        output = []
        info = {
            "testo" : response.json()['question_text'],
            "id"    : response.json()['url'][-2],
        }
        scelte = []
        for choice in data[1:]:
            scelte.append({
                'id' : choice['URL'][-2],
                'testo' : choice['Testo']
            })

        output = {
            'info' :info,
            'scelte':scelte
        }
        #logging.error(data['results'][0]['url'][-2])
        # Puoi passare i dati recuperati dall'API al contesto della vista
        return output
    


""" 
class DetailView(generic.DetailView):
    model = Question
    template_name = "pollsAPI/detail.html"

    def get_queryset(self):
        
        Excludes any questions that aren't published yet.
        
        return Question.objects.filter(pub_date__lte=timezone.now())

class ResultsView(generic.DetailView):
    model = Question
    template_name = "pollsAPI/results.html"

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "pollsAPI/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("results", args=(question.id,)))
"""

def vote(request):
    return HttpResponseRedirect(reverse("index"))