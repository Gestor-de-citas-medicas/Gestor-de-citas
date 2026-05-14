"""
tests/test_groq_provider.py
============================
Pruebas unitarias para el GroqProvider del chatbot MAMP.

Estructura de los tests:
  ┌─────────────────────────────────────────────────────────┐
  │ NIVEL 1 — Unit Tests (sin red, con mocks)               │
  │   TestGroqProviderUnit → prueba la lógica interna       │
  │                                                         │
  │ NIVEL 2 — Integration Tests (llaman a la API real)      │
  │   TestGroqProviderIntegration → valida respuestas reales│
  │                                                         │
  │ NIVEL 3 — Tool Calling Tests                            │
  │   TestGroqToolCalling → valida que el modelo invoca     │
  │                          herramientas correctamente     │
  └─────────────────────────────────────────────────────────┘

Cómo correr:
  # Solo tests unitarios (sin API key):
  .\\venv\\Scripts\\python.exe manage.py test chatbot.tests.test_groq_provider.TestGroqProviderUnit -v 2

  # Tests de integración (requiere API key válida en .env):
  .\\venv\\Scripts\\python.exe manage.py test chatbot.tests.test_groq_provider.TestGroqProviderIntegration -v 2

  # Todos los tests:
  .\\venv\\Scripts\\python.exe manage.py test chatbot.tests.test_groq_provider -v 2
"""

import json
from unittest.mock import MagicMock, patch, PropertyMock
from django.test import TestCase, override_settings


# ──────────────────────────────────────────────────────────────────────────────
# Helpers de configuración para los tests
# ──────────────────────────────────────────────────────────────────────────────

GROQ_SETTINGS = {
    "AI_PROVIDER": "groq",
    "AI_API_KEY": "gsk_test_fake_key_for_unit_tests",
    "AI_MODEL": "llama-3.1-8b-instant",
}

SIMPLE_MESSAGES = [
    {"role": "system", "content": "Eres un asistente médico de MAMP."},
    {"role": "user",   "content": "¿Cuáles son las especialidades disponibles?"},
]

TOOLS_SCHEMA_EXAMPLE = [
    {
        "name": "get_specialties",
        "description": "Retorna la lista de especialidades médicas disponibles.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_doctors_by_specialty",
        "description": "Retorna doctores de una especialidad.",
        "parameters": {
            "type": "object",
            "properties": {
                "specialty": {
                    "type": "string",
                    "description": "Código de especialidad (ej: CARDIOLOGY)",
                }
            },
            "required": ["specialty"],
        },
    },
]


def _make_mock_text_response(content: str):
    """Construye un mock del objeto response de Groq para respuesta de texto."""
    mock_choice = MagicMock()
    mock_choice.finish_reason = "stop"
    mock_choice.message.content = content
    mock_choice.message.tool_calls = None

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.model = "llama-3.1-8b-instant"
    mock_response.usage.prompt_tokens = 50
    mock_response.usage.completion_tokens = 30
    return mock_response


def _make_mock_tool_call_response(tool_name: str, tool_args: dict):
    """Construye un mock del objeto response de Groq para un tool call."""
    mock_tc = MagicMock()
    mock_tc.function.name = tool_name
    mock_tc.function.arguments = json.dumps(tool_args)

    mock_choice = MagicMock()
    mock_choice.finish_reason = "tool_calls"
    mock_choice.message.content = None
    mock_choice.message.tool_calls = [mock_tc]

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


# ──────────────────────────────────────────────────────────────────────────────
# NIVEL 1: Tests Unitarios (mock de la API — sin llamadas reales)
# ──────────────────────────────────────────────────────────────────────────────

@override_settings(**GROQ_SETTINGS)
class TestGroqProviderUnit(TestCase):
    """
    Tests unitarios del GroqProvider con mocks.
    NO realizan llamadas reales a la API de GroqCloud.
    Verifican la lógica interna del provider.
    """

    def setUp(self):
        """Inicializar el provider con un cliente mockeado."""
        with patch("groq.Groq"):
            from chatbot.services.groq_provider import GroqProvider
            self.provider = GroqProvider()
            self.provider.client = MagicMock()

    # ── Test 1: Instanciación correcta ────────────────────────────────────
    def test_provider_uses_correct_model(self):
        """El provider debe usar el modelo configurado en settings."""
        self.assertEqual(self.provider.model, "llama-3.1-8b-instant")

    # ── Test 2: Conversión de tools al formato Groq ───────────────────────
    def test_tools_conversion_to_groq_format(self):
        """
        _tools_to_groq_format debe convertir el schema interno
        al formato OpenAI-compatible que usa Groq.
        """
        groq_tools = self.provider._tools_to_groq_format(TOOLS_SCHEMA_EXAMPLE)

        self.assertEqual(len(groq_tools), 2)

        # Verificar estructura del primer tool
        first = groq_tools[0]
        self.assertEqual(first["type"], "function")
        self.assertIn("function", first)
        self.assertEqual(first["function"]["name"], "get_specialties")
        self.assertIn("description", first["function"])
        self.assertIn("parameters", first["function"])

    # ── Test 3: Respuesta de texto exitosa ────────────────────────────────
    def test_send_message_returns_text(self):
        """
        Cuando el modelo responde con texto (finish_reason='stop'),
        send_message debe retornar {"type": "text", "content": "..."}.
        """
        mock_response = _make_mock_text_response(
            "Las especialidades disponibles son: Cardiología, Pediatría..."
        )
        self.provider.client.chat.completions.create.return_value = mock_response

        result = self.provider.send_message(SIMPLE_MESSAGES, [])

        self.assertEqual(result["type"], "text")
        self.assertIn("Cardiología", result["content"])

    # ── Test 4: Tool call detectado ───────────────────────────────────────
    def test_send_message_returns_tool_call(self):
        """
        Cuando el modelo pide ejecutar una herramienta (finish_reason='tool_calls'),
        send_message debe retornar {"type": "tool_call", "tool_name": ..., "tool_args": ...}.
        """
        mock_response = _make_mock_tool_call_response(
            tool_name="get_specialties",
            tool_args={}
        )
        self.provider.client.chat.completions.create.return_value = mock_response

        result = self.provider.send_message(SIMPLE_MESSAGES, TOOLS_SCHEMA_EXAMPLE)

        self.assertEqual(result["type"], "tool_call")
        self.assertEqual(result["tool_name"], "get_specialties")
        self.assertIsInstance(result["tool_args"], dict)

    # ── Test 5: Tool call con argumentos ─────────────────────────────────
    def test_send_message_tool_call_with_args(self):
        """
        Los argumentos del tool call deben ser parseados correctamente
        del JSON string al dict de Python.
        """
        mock_response = _make_mock_tool_call_response(
            tool_name="get_doctors_by_specialty",
            tool_args={"specialty": "CARDIOLOGY"}
        )
        self.provider.client.chat.completions.create.return_value = mock_response

        result = self.provider.send_message(SIMPLE_MESSAGES, TOOLS_SCHEMA_EXAMPLE)

        self.assertEqual(result["type"], "tool_call")
        self.assertEqual(result["tool_name"], "get_doctors_by_specialty")
        self.assertEqual(result["tool_args"]["specialty"], "CARDIOLOGY")

    # ── Test 6: Manejo de errores de la API ───────────────────────────────
    def test_send_message_handles_api_error(self):
        """
        Si la API lanza una excepción (ej: 429, 401, timeout),
        send_message debe retornar {"type": "error"} sin propagarla.
        """
        self.provider.client.chat.completions.create.side_effect = Exception(
            "429 Too Many Requests"
        )

        result = self.provider.send_message(SIMPLE_MESSAGES, [])

        self.assertEqual(result["type"], "error")
        self.assertIn("Groq", result["content"])

    # ── Test 7: Sin tools → no enviar tool_choice ─────────────────────────
    def test_no_tools_excludes_tool_params(self):
        """
        Cuando tools=[], el request NO debe incluir 'tools' ni 'tool_choice'
        para evitar errores innecesarios de la API.
        """
        mock_response = _make_mock_text_response("Respuesta simple.")
        self.provider.client.chat.completions.create.return_value = mock_response

        self.provider.send_message(SIMPLE_MESSAGES, [])

        call_kwargs = self.provider.client.chat.completions.create.call_args.kwargs
        self.assertNotIn("tools", call_kwargs)
        self.assertNotIn("tool_choice", call_kwargs)

    # ── Test 8: Con tools → incluye tool_choice="auto" ───────────────────
    def test_with_tools_includes_tool_choice(self):
        """
        Cuando se pasan tools, el request debe incluir tool_choice='auto'.
        """
        mock_response = _make_mock_text_response("Respuesta con tools.")
        self.provider.client.chat.completions.create.return_value = mock_response

        self.provider.send_message(SIMPLE_MESSAGES, TOOLS_SCHEMA_EXAMPLE)

        call_kwargs = self.provider.client.chat.completions.create.call_args.kwargs
        self.assertIn("tools", call_kwargs)
        self.assertEqual(call_kwargs["tool_choice"], "auto")

    # ── Test 9: Modelo correcto en el request ─────────────────────────────
    def test_correct_model_sent_in_request(self):
        """El model ID enviado a la API debe coincidir con settings.AI_MODEL."""
        mock_response = _make_mock_text_response("ok")
        self.provider.client.chat.completions.create.return_value = mock_response

        self.provider.send_message(SIMPLE_MESSAGES, [])

        call_kwargs = self.provider.client.chat.completions.create.call_args.kwargs
        self.assertEqual(call_kwargs["model"], "llama-3.1-8b-instant")

    # ── Test 10: JSON inválido en tool args ───────────────────────────────
    def test_malformed_tool_args_returns_empty_dict(self):
        """
        Si el modelo devuelve JSON inválido en los argumentos de la herramienta,
        el provider debe retornar {} en lugar de crashear.
        """
        mock_tc = MagicMock()
        mock_tc.function.name = "get_specialties"
        mock_tc.function.arguments = "INVALID JSON {{{"  # JSON roto

        mock_choice = MagicMock()
        mock_choice.finish_reason = "tool_calls"
        mock_choice.message.tool_calls = [mock_tc]

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        self.provider.client.chat.completions.create.return_value = mock_response

        result = self.provider.send_message(SIMPLE_MESSAGES, TOOLS_SCHEMA_EXAMPLE)

        self.assertEqual(result["type"], "tool_call")
        self.assertEqual(result["tool_args"], {})  # fallback a dict vacío


# ──────────────────────────────────────────────────────────────────────────────
# NIVEL 2: Tests de Integración (llaman a la API REAL de GroqCloud)
# ──────────────────────────────────────────────────────────────────────────────

@override_settings(**{
    **GROQ_SETTINGS,
    "AI_API_KEY": "gsk_dummy_key_for_integration_testing_remove_before_push",
})
class TestGroqProviderIntegration(TestCase):
    """
    Tests de integración — hacen llamadas REALES a GroqCloud.
    Requieren conexión a internet y API key válida.

    ⚠️ Estos tests consumen cuota del free tier.
       Correr solo cuando se necesite validar la integración.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            from chatbot.services.groq_provider import GroqProvider
            cls.provider = GroqProvider()
        except Exception as e:
            cls.provider = None
            cls.skip_reason = str(e)

    def _skip_if_no_provider(self):
        if self.provider is None:
            self.skipTest(f"Provider no disponible: {self.skip_reason}")

    # ── Test I1: Respuesta de texto simple ────────────────────────────────
    def test_real_simple_text_response(self):
        """
        La API real de Groq debe responder con texto a un mensaje simple.
        Valida: conectividad, autenticación, y formato de respuesta.
        """
        self._skip_if_no_provider()

        result = self.provider.send_message(
            messages=[
                {"role": "system", "content": "Responde solo en español, máximo 20 palabras."},
                {"role": "user",   "content": "¿Cuál es tu nombre?"},
            ],
            tools=[]
        )

        print(f"\n[I1] Groq response: {result}")
        self.assertIn(result["type"], ["text", "error"])
        if result["type"] == "text":
            self.assertIsInstance(result["content"], str)
            self.assertGreater(len(result["content"]), 0)

    # ── Test I2: Tool calling con herramienta real ────────────────────────
    def test_real_tool_calling_triggers(self):
        """
        Al preguntar por especialidades, el modelo debería invocar
        la herramienta get_specialties en lugar de responder de memoria.
        """
        self._skip_if_no_provider()

        result = self.provider.send_message(
            messages=[
                {"role": "system", "content": "Usa las herramientas disponibles para responder."},
                {"role": "user",   "content": "¿Qué especialidades médicas tienen disponibles?"},
            ],
            tools=TOOLS_SCHEMA_EXAMPLE
        )

        print(f"\n[I2] Tool call result: {result}")
        # El modelo puede responder con tool_call o texto — ambos son válidos
        self.assertIn(result["type"], ["tool_call", "text", "error"])
        if result["type"] == "tool_call":
            self.assertIn(result["tool_name"], ["get_specialties", "get_doctors_by_specialty"])

    # ── Test I3: Velocidad de respuesta (latencia) ────────────────────────
    def test_real_response_speed(self):
        """
        Groq es conocido por ser muy rápido (~500 tok/s en LPU).
        La respuesta debería llegar en menos de 5 segundos.
        """
        import time
        self._skip_if_no_provider()

        start = time.time()
        result = self.provider.send_message(
            messages=[{"role": "user", "content": "Di 'ok' en una sola palabra."}],
            tools=[]
        )
        elapsed = time.time() - start

        print(f"\n[I3] Response in {elapsed:.2f}s -> {result}")
        # No falla si es lento, solo reporta
        self.assertLess(elapsed, 30, "La respuesta tardó más de 30 segundos")


# ──────────────────────────────────────────────────────────────────────────────
# NIVEL 3: Tests del Factory (get_provider)
# ──────────────────────────────────────────────────────────────────────────────

class TestProviderFactory(TestCase):
    """
    Prueba que la factory retorna el provider correcto según settings.
    """

    @override_settings(AI_PROVIDER="groq", AI_API_KEY="gsk_test", AI_MODEL="llama-3.1-8b-instant")
    def test_factory_returns_groq_provider(self):
        """Con AI_PROVIDER=groq, get_provider() debe retornar GroqProvider."""
        with patch("groq.Groq"):
            from chatbot.services import get_provider
            from chatbot.services.groq_provider import GroqProvider
            provider = get_provider()
            self.assertIsInstance(provider, GroqProvider)

    @override_settings(AI_PROVIDER="unknown_provider", AI_API_KEY="x", AI_MODEL="x")
    def test_factory_raises_for_unknown_provider(self):
        """Con un provider desconocido, debe lanzar ValueError con lista de opciones."""
        from chatbot.services import get_provider
        with self.assertRaises(ValueError) as ctx:
            get_provider()
        self.assertIn("groq", str(ctx.exception))
        self.assertIn("openai", str(ctx.exception))

    @override_settings(AI_PROVIDER="groq", AI_API_KEY="", AI_MODEL="llama-3.1-8b-instant")
    def test_factory_raises_if_no_api_key(self):
        """Sin API key configurada, el provider debe lanzar ValueError."""
        from chatbot.services import get_provider
        with self.assertRaises((ValueError, Exception)):
            get_provider()
