from typing import Any, Mapping, Optional, Type, Union
from django import forms
from django.forms.utils import ErrorList
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth.hashers import Argon2PasswordHasher, make_password, check_password
import logging

import requests

url_api = "http://localhost:8000"

class RegisterForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    email = forms.EmailField()

    def formMethod(self, session):
        
        data = {
            "username" : self.cleaned_data['username'],
            "email" : self.cleaned_data['email'],
            "password" : self.cleaned_data['password']
        }
        response = requests.post(url_api+reverse('APIregister'), data)  # Sostituisci l'URL con l'API reale che desideri chiamare
        data = response.json()
        if response.status_code == 400:
            if 'username' in data:
                errore = str(data['username'])
            elif 'email' in data:
                errore = str(data['email'])
            else:
                errore = str(data['error'])
            return { 'error' : errore}
        elif response.status_code == 500:
            return {'error' : str(data['Exception'])}
        else:
            session['token'] = data['token']
            session['username'] = data['username']
            session['email'] = data['email']
            return { 'success' : "Registered successfully"}

class LoginForm(forms.Form):
    info = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def formMethod(self, session):
        data = {
            "info" : self.cleaned_data['info'],
            "password" : self.cleaned_data['password']
        }
        response = requests.post(url_api+reverse('APIlogin'), data)
        data = response.json() 
        if response.status_code == 400 or response.status_code == 404:
            return { 'error' : str(data['error'])}
        elif response.status_code == 500:
            return {'error' : str(data['Exception'])}
        else:
            session['token'] = data['token']
            session['username'] = data['username']
            session['email'] = data['email']
            return { 'success' : "Logged in successfully"}
        
class newPollForm(forms.Form):
    question_text = forms.CharField(label="Domanda del sondaggio")
    owner = forms.CharField(label="Proprietario del sondaggio, lasciare vuoto per inserire sé stessi", required=False)
    initial_data = {}


    def newPoll(self, session):
        if self.cleaned_data['owner'].strip() == "":
            self.cleaned_data['owner'] = session['username']
        return self.cleaned_data
    
class editPollForm(forms.Form):
    question_text = forms.CharField(label="Domanda del sondaggio")
    owner = forms.CharField(label="Proprietario del sondaggio, lasciare vuoto per inserire sé stessi", required=False)
    initial_data = {}
    def __init__(self, *args, **kwargs):
        data = kwargs.pop('data', {})
        self.initial_data = data
        choices = data['choices']
        super(editPollForm, self).__init__(*args, **kwargs)
        self.fields["question_text"].initial = data['question_text']
        self.fields["owner"].initial = data['owner']
        for i, choice in enumerate(choices):
            self.fields[f"choice_text{i}"] = forms.CharField(
                initial=choice['choice_text'],
                label=f"Scelta {i + 1}"
            )
            self.fields[f"votes{i}"] = forms.IntegerField(
                initial=int(choice['votes']),
                label="Numero voti"
            )

    


