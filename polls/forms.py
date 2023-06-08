from django import forms
from django.shortcuts import redirect
from django.contrib.auth.hashers import Argon2PasswordHasher, make_password, check_password
import logging

import requests


class RegisterForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    email = forms.EmailField()

    def register(self):
        password = self.cleaned_data['password']
        data = {
            "username" : self.cleaned_data['username'],
            "email" : self.cleaned_data['email'],
            "password" : make_password(password)
        }
        response = requests.post('http://127.0.0.1:8000/api/users/', data)  # Sostituisci l'URL con l'API reale che desideri chiamare
        if response.status_code == 400:
            data = response.json()
            if 'username' in data:
                errore = str(data['username'])
            elif 'email' in data:
                errore = str(data['email'])
            return { 'error' : errore}
        else:
            start = response.status_code // 100
            if start >= 4:
                return {'error' : "C'è stato un errore"}
            else:
                return { 'success' : "Registered successfully"}

class LoginForm(forms.Form):
    info = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def login(self):
        password = self.cleaned_data['password']
        info = self.cleaned_data['info']
        response = requests.get('http://127.0.0.1:8000/api/userInfo/'+str(info))
        if response.status_code == 500:
            return False
        data = response.json()
        logging.warning(data)
        return check_password(password, data['password'])