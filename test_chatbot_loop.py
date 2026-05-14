import os, sys, django, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
sys.path.insert(0, '.')
django.setup()

from chatbot.services import get_provider
from chatbot.tools import TOOLS_SCHEMA, dispatch_tool, get_specialties
from accounts.models import User

print('=== TEST 1: get_specialties direct ===')
specs = get_specialties()
print(json.dumps(specs, indent=2, ensure_ascii=False))

print()
print('=== TEST 2: Full AI tool-calling loop ===')
provider = get_provider()
print('Provider:', provider.__class__.__name__, '| Model:', provider.model)

user = User.objects.filter(role='PATIENT').first()
print('Patient:', user)

messages = [
    {'role': 'system', 'content': 'Eres asistente medico MAMP. Usa las herramientas para responder.'},
    {'role': 'user', 'content': 'Que especialidades medicas tienen disponibles?'},
]

for i in range(3):
    result = provider.send_message(messages, TOOLS_SCHEMA)
    print(f'Iteration {i+1}: type={result["type"]}')

    if result['type'] == 'text':
        print('FINAL RESPONSE:', result['content'][:400])
        break
    elif result['type'] == 'tool_call':
        tool_name = result['tool_name']
        tool_args = result.get('tool_args') or {}
        tool_call_id = result.get('tool_call_id', 'call_123')
        print(f'  Tool called: {tool_name} | Args: {tool_args}')
        tool_result = dispatch_tool(tool_name, tool_args, user)
        tool_result_str = json.dumps(tool_result, ensure_ascii=False, default=str)
        print(f'  Tool result: {tool_result_str[:300]}')
        messages.append({
            'role': 'assistant',
            'content': None,
            'tool_calls': [{
                'id': tool_call_id,
                'type': 'function',
                'function': {
                    'name': tool_name,
                    'arguments': json.dumps(tool_args)
                }
            }]
        })
        messages.append({
            'role': 'tool',
            'tool_call_id': tool_call_id,
            'name': tool_name,
            'content': tool_result_str
        })
    elif result['type'] == 'error':
        print('ERROR:', result['content'])
        break
