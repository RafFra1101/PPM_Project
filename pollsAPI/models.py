import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib import admin


class Poll(models.Model):
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="owner", to_field="username", null=True)
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")
    def __str__(self):
        return self.question_text
    

class Choice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    users = models.ManyToManyField(User)
    votes = models.IntegerField()
    def __str__(self):
        return self.choice_text
    
