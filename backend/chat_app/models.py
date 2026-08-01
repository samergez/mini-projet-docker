from django.db import models

class ChatMessage(models.Model):
    prompt = models.TextField()
    response = models.TextField()
    metadata = models.JSONField(default=dict, blank=True) # Stockage des métadonnées
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message {self.id} - {self.created_at}"