import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib import admin


class Poll(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")
    def __str__(self):
        return self.question_text
    @admin.display(boolean = True, ordering="pub_date", description="Published recently?",)
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now
    

class Choice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    users = models.ManyToManyField(User)
    choice_text = models.CharField(max_length=200)
    def __str__(self):
        return self.choice_text
    
