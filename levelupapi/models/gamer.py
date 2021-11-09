from django.db import models
from django.contrib.auth.models import User
from django.db.models.deletion import CASCADE


class Gamer(models.Model):

    user = models.OneToOneField(User, on_delete=CASCADE)
    bio = models.CharField(max_length=50)
