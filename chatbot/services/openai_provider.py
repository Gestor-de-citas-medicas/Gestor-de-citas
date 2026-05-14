"""
openai_provider.py — Implementación para OpenAI (GPT-4o-mini, GPT-4o, etc.)
Usa la API oficial de OpenAI con function-calling nativo.
"""
import json
from django.conf import settings
from .base_provider import BaseAIProvider


class OpenAIProvider(BaseAIProvider):
    """Proveedor usando la API de OpenAI con function-calling."""

    def __init__(self):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Instala openai: pip install openai")

        self.client = OpenAI(api_key=settings.AI_API_KEY)
        self.model = getattr(settings, "AI_MODEL", "gpt-4o-mini")

    def _tools_to_openai_format(self, tools):
        """Convierte TOOLS_SCHEMA al formato de function-calling de OpenAI."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                },
            }
            for t in tools
        ]

    def send_message(self, messages, tools):
        try:
            openai_tools = self._tools_to_openai_format(tools) if tools else None

            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.4,
            }
            if openai_tools:
                kwargs["tools"] = openai_tools
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            message = choice.message

            # Si la IA quiere usar un tool
            if choice.finish_reason == "tool_calls" and message.tool_calls:
                tool_call = message.tool_calls[0]
                return {
                    "type": "tool_call",
                    "tool_name": tool_call.function.name,
                    "tool_args": json.loads(tool_call.function.arguments),
                }

            # Respuesta de texto normal
            return {
                "type": "text",
                "content": message.content or "",
            }

        except Exception as e:
            return {
                "type": "error",
                "content": f"Error con OpenAI: {str(e)}",
            }
