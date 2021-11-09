from django.db import models
from django.db.models.deletion import CASCADE


class Game(models.Model):

    game_type = models.ForeignKey("GameType", on_delete=CASCADE)
    title = models.CharField(max_length=50)
    maker = models.CharField(max_length=50)
    gamer = models.ForeignKey("Gamer", on_delete=CASCADE)
    number_of_players = models.IntegerField()
    skill_level = models.IntegerField()
