from django.db import models

class TTLockCredential(models.Model):
    client_id = models.CharField(max_length=128)
    client_secret = models.CharField(max_length=128)
    username = models.CharField(max_length=64)
    password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.client_id})"
