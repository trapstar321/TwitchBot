from django.db import models
from django.contrib.auth.models import User

# Create your models here.
#this is just for ContentType for Admin permission
class Admin(models.Model):
    pass

# this is a one-to-one User mapped table for storing token for websocket server
# web socket server receives the token and checks permissions in database
class Token(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=10)

class IRCSetup(models.Model):
    ip = models.CharField(max_length=100)
    port = models.IntegerField(default=0)
    oauth_token = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    channel = models.CharField(max_length=100)