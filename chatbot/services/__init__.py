"""
Factory que selecciona el proveedor de IA según settings.AI_PROVIDER.
Añadir un nuevo proveedor = crear su archivo y registrarlo aquí.

Proveedores disponibles:
  'openai' → OpenAIProvider  (GPT-4o-mini)
  'gemini' → GeminiProvider  (gemini-2.0-flash)
  'groq'   → GroqProvider    (llama-3.1-8b-instant) ← más económico, free tier
"""
from django.conf import settings
from .base_provider import BaseAIProvider


def get_provider():
    """
    Retorna la instancia del proveedor de IA configurado en .env / settings.

    Uso:
        # .env
        AI_PROVIDER=groq
        AI_API_KEY=gsk_...
        AI_MODEL=llama-3.1-8b-instant
    """
    provider_name = getattr(settings, "AI_PROVIDER", "groq").lower()

    if provider_name == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider()

    elif provider_name == "gemini":
        from .gemini_provider import GeminiProvider
        return GeminiProvider()

    elif provider_name == "groq":
        from .groq_provider import GroqProvider
        return GroqProvider()

    else:
        raise ValueError(
            f"Proveedor de IA desconocido: '{provider_name}'. "
            f"Opciones válidas: openai, gemini, groq"
        )
