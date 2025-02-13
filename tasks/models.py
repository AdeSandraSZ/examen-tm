from django.contrib.auth.models import AbstractUser 
from django.db import models

# Create your models here.
class Position(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)


class User(AbstractUser):
    is_agent = models.BooleanField(default=False)
##    pass 