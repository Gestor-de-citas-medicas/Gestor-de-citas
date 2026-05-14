"""
views.py — Vistas del chatbot.
  - chat_message: endpoint POST principal (recibe mensaje, retorna respuesta IA)
  - chat_history: GET para recuperar historial
  - chat_clear: POST para limpiar historial
"""
import json
import logging

logger = logging.getLogger(__name__)
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import ChatSession, ChatMessage
from .system_prompt import SYSTEM_PROMPT
from .tools import TOOLS_SCHEMA, dispatch_tool
from .services import get_provider


def _get_or_create_session(user):
    """Obtiene o crea la sesión de chat del paciente."""
    session, _ = ChatSession.objects.get_or_create(patient=user)
    return session


def _build_messages_for_provider(session):
    """
    Construye la lista de mensajes en formato estándar para cualquier provider.
    Incluye el system prompt + los últimos 20 mensajes del historial.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    history = session.messages.order_by("-created_at")[:20]
    for msg in reversed(list(history)):
        if msg.role == ChatMessage.Role.TOOL:
            messages.append({
                "role": "user", 
                "content": f"Resultado de la herramienta {msg.tool_name or 'desconocida'}: {msg.content}\nUsa esta información para continuar."
            })
        else:
            messages.append({"role": msg.role, "content": msg.content})

    return messages


def _patient_required(view_func):
    """Decorator: solo pacientes autenticados pueden usar el chatbot."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != "PATIENT":
            return JsonResponse(
                {"error": "El chatbot solo está disponible para pacientes."},
                status=403
            )
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    wrapper.__doc__ = view_func.__doc__
    return wrapper


@_patient_required
@require_http_methods(["POST"])
def chat_message(request):
    """
    Endpoint principal del chatbot.
    POST /chatbot/message/
    Body JSON: {"message": "Quiero agendar una cita"}
    """
    try:
        body = json.loads(request.body)
        user_message = body.get("message", "").strip()
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"error": "JSON inválido."}, status=400)

    if not user_message:
        return JsonResponse({"error": "El mensaje no puede estar vacío."}, status=400)

    if len(user_message) > 2000:
        return JsonResponse({"error": "Mensaje demasiado largo."}, status=400)

    session = _get_or_create_session(request.user)

    # Guardar el mensaje del usuario
    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.USER,
        content=user_message,
    )

    # Construir historial para el provider
    messages = _build_messages_for_provider(session)

    try:
        provider = get_provider()
    except Exception as e:
        return JsonResponse({"error": f"Error iniciando proveedor IA: {str(e)}"}, status=500)

    # ── Loop de tool-calling ─────────────────────────────────────
    # La IA puede invocar múltiples herramientas antes de responder.
    MAX_ITERATIONS = 5
    final_response = None

    for _ in range(MAX_ITERATIONS):
        result = provider.send_message(messages, TOOLS_SCHEMA)

        if result["type"] == "text":
            final_response = result["content"]
            break

        elif result["type"] == "tool_call":
            tool_name = result["tool_name"]
            # Groq returns None for tools with no params — normalize to {}
            tool_args = result.get("tool_args") or {}
            tool_call_id = result.get("tool_call_id", "call_123")

            logger.info("[Chatbot] Tool call: %s | args: %s", tool_name, tool_args)

            # Ejecutar el tool
            tool_result = dispatch_tool(tool_name, tool_args, request.user)
            tool_result_str = json.dumps(tool_result, ensure_ascii=False, default=str)

            logger.info("[Chatbot] Tool result: %s", tool_result_str[:200])

            # Guardar en BD
            ChatMessage.objects.create(
                session=session,
                role=ChatMessage.Role.TOOL,
                content=tool_result_str,
                tool_name=tool_name,
            )

            # Añadir al historial para la siguiente iteración
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": tool_call_id,
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": json.dumps(tool_args)
                    }
                }]
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": tool_result_str,
            })

        elif result["type"] == "error":
            logger.error("[Chatbot] Provider error: %s", result.get("content", ""))
            final_response = "Lo siento, ocurrió un error procesando tu solicitud. ¿Puedes intentarlo de nuevo?"
            break

    if final_response is None:
        final_response = "Lo siento, no pude generar una respuesta en este momento."

    # Guardar la respuesta del asistente
    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.ASSISTANT,
        content=final_response,
    )

    return JsonResponse({
        "message": final_response,
        "session_id": session.pk,
    })


@_patient_required
@require_http_methods(["GET"])
def chat_history(request):
    """GET /chatbot/history/ — últimos 30 mensajes de la sesión."""
    session = _get_or_create_session(request.user)
    messages = session.messages.filter(
        role__in=[ChatMessage.Role.USER, ChatMessage.Role.ASSISTANT]
    ).order_by("created_at")[:30]

    return JsonResponse({
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
            }
            for msg in messages
        ]
    })


@_patient_required
@require_http_methods(["POST"])
def chat_clear(request):
    """POST /chatbot/clear/ — borra historial."""
    session = _get_or_create_session(request.user)
    session.messages.all().delete()
    return JsonResponse({"ok": True, "message": "Historial borrado."})
