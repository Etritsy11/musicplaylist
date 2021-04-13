from django.db import models
from django.contrib.auth.models import User


class MusicPlaylist(models.Model):
    title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Video(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField()
    youtube_id = models.CharField(max_length=255)
    playlist = models.ForeignKey(MusicPlaylist, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)
