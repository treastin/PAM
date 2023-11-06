from django.db import models

# Create your models here.


class Log(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(max_length=32)
    details = models.JSONField()
    error_message = models.TextField(null=True)
