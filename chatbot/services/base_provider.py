"""
base_provider.py — Clase abstracta que deben implementar todos los providers de IA.
Cambiar de OpenAI a Gemini = solo cambiar AI_PROVIDER en .env.
"""
from abc import ABC, abstractmethod


class BaseAIProvider(ABC):
    """
    Interfaz unificada para proveedores de IA.
    Cada proveedor concreto implementa `send_message` con su SDK propio.
    """

    @abstractmethod
    def send_message(self, messages, tools):
        """
        Envía una lista de mensajes al modelo y retorna la respuesta normalizada.

        Args:
            messages: Lista de dicts [{"role": "user"|"assistant"|"tool", "content": "..."}]
            tools: Lista de herramientas disponibles en formato TOOLS_SCHEMA.

        Returns:
            dict con una de estas estructuras:
            - Texto:      {"type": "text", "content": "Hola, ¿en qué te ayudo?"}
            - Tool call:  {"type": "tool_call", "tool_name": "...", "tool_args": {...}}
            - Error:      {"type": "error", "content": "Descripción del error"}
        """
        ...
