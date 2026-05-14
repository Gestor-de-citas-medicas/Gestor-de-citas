"""
groq_provider.py — Proveedor GroqCloud para el chatbot MAMP.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
¿QUÉ ES GROQCLOUD?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GroqCloud es una plataforma de inferencia de LLMs de ultra-baja latencia.
Utiliza hardware propietario "LPU" (Language Processing Unit) que es
significativamente más rápido que las GPUs convencionales para tokens de texto.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
¿CÓMO SE LLAMA EL MODELO?  →  Model ID
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Groq usa model IDs directos. Ejemplos:

  FREE TIER (más económico):
  ┌──────────────────────────────┬─────────────────────────────────────────────┐
  │ Model ID                     │ Descripción                                 │
  ├──────────────────────────────┼─────────────────────────────────────────────┤
  │ llama-3.1-8b-instant         │ ★ MÁS ECONÓMICO — 8B params, ultra-rápido   │
  │                              │   14,400 req/día, 6,000 tokens/min GRATIS   │
  ├──────────────────────────────┼─────────────────────────────────────────────┤
  │ llama-3.3-70b-versatile      │ 70B params, más inteligente, mismo free     │
  │                              │   1,000 req/día, 6,000 tokens/min GRATIS    │
  ├──────────────────────────────┼─────────────────────────────────────────────┤
  │ llama-4-scout-17b-16e-instruct│ Preview: Llama 4, multimodal, 17B MoE      │
  └──────────────────────────────┴─────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
¿CÓMO FUNCIONA LA API?  →  100% Compatible con OpenAI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
La API de Groq es IDÉNTICA a la de OpenAI, solo cambia la base_url:
  - OpenAI:  https://api.openai.com/v1
  - Groq:    https://api.groq.com/openai/v1

El SDK oficial `groq` es un wrapper del SDK de OpenAI con la URL pre-configurada.
También puedes usar el SDK de OpenAI directamente apuntando a Groq.

Ejemplo minimal:
  from groq import Groq
  client = Groq(api_key="gsk_...")
  response = client.chat.completions.create(
      model="llama-3.1-8b-instant",
      messages=[{"role": "user", "content": "Hola"}],
      tools=[...],         ← tool calling igual que OpenAI
      tool_choice="auto",
  )

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
from django.conf import settings
from .base_provider import BaseAIProvider


# ── Modelos disponibles en Groq Free Tier ──────────────────────────────────
GROQ_FREE_MODELS = {
    # Más económico: 14,400 req/day, fastest inference (~500 tok/s)
    "llama-3.1-8b-instant": {
        "params": "8B", "context": "128k", "req_per_day": 14_400,
        "tokens_per_min": 6_000, "recommended_for": "chatbots, respuestas rápidas"
    },
    # Más inteligente: 1,000 req/day, muy buena calidad
    "llama-3.3-70b-versatile": {
        "params": "70B", "context": "128k", "req_per_day": 1_000,
        "tokens_per_min": 6_000, "recommended_for": "tareas complejas, razonamiento"
    },
    # Nuevo Llama 4 (preview): Mixture of Experts
    "meta-llama/llama-4-scout-17b-16e-instruct": {
        "params": "17B MoE", "context": "128k", "req_per_day": 1_000,
        "tokens_per_min": 6_000, "recommended_for": "tareas avanzadas, preview"
    },
}

# Modelo por defecto — el más económico con más cuota gratis
DEFAULT_MODEL = "llama-3.1-8b-instant"


class GroqProvider(BaseAIProvider):
    """
    Proveedor GroqCloud usando el SDK oficial `groq`.
    API 100% compatible con OpenAI → tool calling idéntico.
    """

    def __init__(self):
        try:
            from groq import Groq
        except ImportError:
            raise ImportError(
                "Instala el SDK de Groq: pip install groq"
            )

        api_key = getattr(settings, "AI_API_KEY", "")
        if not api_key:
            raise ValueError("AI_API_KEY no está configurada en .env / settings.py")

        self.client = Groq(api_key=api_key)
        self.model = getattr(settings, "AI_MODEL", DEFAULT_MODEL)

    def _tools_to_groq_format(self, tools):
        """
        Convierte TOOLS_SCHEMA al formato de function calling de Groq.
        Es idéntico al formato de OpenAI:
          [{"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}]
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                }
            }
            for t in tools
        ]

    def send_message(self, messages, tools):
        """
        Envía mensajes a GroqCloud y retorna respuesta normalizada.

        Groq maneja tool calling en un solo request — devuelve:
          - finish_reason == "tool_calls"  → hay una función a ejecutar
          - finish_reason == "stop"        → respuesta de texto final
        """
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1024,
            }

            # Solo agrega tools si hay herramientas disponibles
            if tools:
                kwargs["tools"] = self._tools_to_groq_format(tools)
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**kwargs)
            choice = response.choices[0]

            # ── Tool call: la IA quiere ejecutar una herramienta ──
            if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
                tc = choice.message.tool_calls[0]  # tomamos la primera
                tool_name = tc.function.name
                tool_call_id = tc.id
                try:
                    raw_args = tc.function.arguments
                    if raw_args is None or raw_args == "":
                        tool_args = {}
                    else:
                        tool_args = json.loads(raw_args)
                except (json.JSONDecodeError, TypeError):
                    tool_args = {}

                return {
                    "type": "tool_call",
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "tool_call_id": tool_call_id,
                }

            # ── Respuesta de texto ──
            content = choice.message.content or ""
            return {
                "type": "text",
                "content": content,
            }

        except Exception as e:
            return {
                "type": "error",
                "content": f"Error con Groq ({self.model}): {str(e)}",
            }
