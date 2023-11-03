from django.db import models

# Create your models here.


class Log(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=32)
    details = models.JSONField()
