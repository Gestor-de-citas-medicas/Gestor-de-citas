from django.contrib import admin
from .models import ChatSession, ChatMessage


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("role", "content", "tool_name", "created_at")
    ordering = ("-created_at",)


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("patient", "created_at", "updated_at", "message_count")
    readonly_fields = ("created_at", "updated_at")
    inlines = [ChatMessageInline]

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = "Mensajes"


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("session", "role", "short_content", "tool_name", "created_at")
    list_filter = ("role",)
    readonly_fields = ("created_at",)

    def short_content(self, obj):
        return obj.content[:80]
    short_content.short_description = "Contenido"
