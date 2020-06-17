import uuid

from django.db import models

# Create your models here.

class ClassifierVote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    classifier = models.CharField(max_length=250) 
    vote_id = models.CharField(max_length=250)

class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asker = models.CharField(max_length=255)
    votes = models.ManyToManyField(ClassifierVote, blank=True, null=True)
    question_text = models.CharField(max_length=250)
    suggestion_correct = models.BooleanField(default=True)
    answer = models.CharField(max_length=250, default="")
    was_misclassified = models.BooleanField(default=False)
    message_id = models.CharField(max_length=500, default="")
    room_id = models.CharField(max_length=500, default="")