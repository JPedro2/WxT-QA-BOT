from django.contrib import admin

from .models import ClassifierVote, Question
# Register your models here.

admin.site.register(ClassifierVote)
admin.site.register(Question)
