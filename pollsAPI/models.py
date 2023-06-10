import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib import admin


class Poll(models.Model):
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="owner", to_field="username", null=True)
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")
    users = models.ManyToManyField(User)
    def __str__(self):
        return self.question_text
    @admin.display(boolean = True, ordering="pub_date", description="Published recently?",)
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now
    

class Choice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    def __str__(self):
        return self.choice_text
    