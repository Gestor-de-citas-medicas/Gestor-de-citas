"""
gemini_provider.py — Implementación para Google Gemini (gemini-2.0-flash, etc.)
Usa el SDK oficial google-genai (nuevo, reemplaza google-generativeai).
"""
import json
from django.conf import settings
from .base_provider import BaseAIProvider


class GeminiProvider(BaseAIProvider):
    """Proveedor usando la API de Google Gemini con function declarations."""

    def __init__(self):
        try:
            from google import genai
        except ImportError:
            raise ImportError("Instala google-genai: pip install google-genai")

        self.client = genai.Client(api_key=settings.AI_API_KEY)
        self.model_name = getattr(settings, "AI_MODEL", "gemini-2.0-flash")

    def _tools_to_gemini_format(self, tools):
        """Convierte TOOLS_SCHEMA al formato de function declarations de google-genai."""
        from google.genai import types

        declarations = []
        for t in tools:
            declarations.append(types.FunctionDeclaration(
                name=t["name"],
                description=t["description"],
                parameters=t["parameters"],
            ))
        return [types.Tool(function_declarations=declarations)]

    def _build_contents(self, messages):
        """
        Convierte mensajes al formato de google-genai.
        Separa system instruction del historial.
        """
        from google.genai import types

        system_content = ""
        contents = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                system_content = content
            elif role == "user":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=content)]
                ))
            elif role == "assistant":
                contents.append(types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=content)]
                ))
            elif role == "tool":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=f"[Resultado de herramienta]: {content}")]
                ))

        return contents, system_content

    def send_message(self, messages, tools):
        try:
            from google.genai import types

            contents, system_content = self._build_contents(messages)
            gemini_tools = self._tools_to_gemini_format(tools) if tools else None

            config = types.GenerateContentConfig(
                system_instruction=system_content if system_content else None,
                tools=gemini_tools,
                temperature=0.4,
                max_output_tokens=1024,
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )

            # Verificar si hay function call
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        fc = part.function_call
                        return {
                            "type": "tool_call",
                            "tool_name": fc.name,
                            "tool_args": dict(fc.args) if fc.args else {},
                        }

            # Respuesta de texto
            return {
                "type": "text",
                "content": response.text or "",
            }

        except Exception as e:
            return {
                "type": "error",
                "content": f"Error con Gemini: {str(e)}",
            }
