from django.db import models
from django.conf import settings


class ChatSession(models.Model):
    """Una sesión de conversación por usuario. Se crea automáticamente la primera vez."""
    patient = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_session",
        limit_choices_to={"role": "PATIENT"},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session({self.patient.username})"


class ChatMessage(models.Model):
    """Un mensaje individual dentro de una sesión."""

    class Role(models.TextChoices):
        USER      = "user",      "Usuario"
        ASSISTANT = "assistant", "Asistente"
        TOOL      = "tool",      "Herramienta"

    session    = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role       = models.CharField(max_length=20, choices=Role.choices)
    content    = models.TextField()
    tool_name  = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        preview = self.content[:60]
        return f"[{self.role}] {preview}"
