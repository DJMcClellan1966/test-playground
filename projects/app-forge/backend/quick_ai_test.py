"""Quick comparison: App Forge vs phi3:mini"""
import json, time, urllib.request, sys
sys.path.insert(0, '.')
from template_registry import match_template_intent, TEMPLATE_REGISTRY

TEMPLATES = [t.id for t in TEMPLATE_REGISTRY]

def query_ai(desc, model='qwen2.5:7b'):
    prompt = f'''Pick ONE template for: "{desc}"
Options: {TEMPLATES}
Reply with just the template name, nothing else.'''
    data = json.dumps({
        'model': model, 
        'prompt': prompt, 
        'stream': False, 
        'options': {'temperature': 0.1, 'num_predict': 30}
    }).encode()
    try:
        req = urllib.request.Request('http://localhost:11434/api/generate', 
                                     data=data, headers={'Content-Type':'application/json'})
        r = urllib.request.urlopen(req, timeout=90)
        resp = json.loads(r.read()).get('response', '').lower().strip()
        # Find first matching template in response
        for t in TEMPLATES:
            if t in resp: 
                return t
        return f'[{resp[:25]}]'
    except Exception as e:
        return f'[timeout]'

tests = [
    'a wordle clone',
    'tic tac toe game', 
    'reaction time with different colored tiles',
    'click correct color quickly',
    'a recipe collection app',
    'number guessing game',
    'memory card matching',
]

print('=' * 75)
print('APP FORGE vs qwen2.5:7b - Head to Head Comparison')
print('=' * 75)
print(f'Templates available: {len(TEMPLATES)}')
print(TEMPLATES)
print()

match_count = 0
forge_total_ms = 0
ai_total_ms = 0

for desc in tests:
    # App Forge
    t0 = time.time()
    forge_id, _, _ = match_template_intent(desc)
    forge_ms = (time.time() - t0) * 1000
    forge_total_ms += forge_ms
    
    # AI Model
    print(f'Testing: "{desc[:45]}"...', flush=True)
    t0 = time.time()
    ai_id = query_ai(desc)
    ai_ms = (time.time() - t0) * 1000
    ai_total_ms += ai_ms
    
    ok = '✓ AGREE' if forge_id == ai_id else '✗ DIFFER'
    if forge_id == ai_id: 
        match_count += 1
    
    print(f'  Forge: {forge_id:<15} ({forge_ms:.0f}ms)')
    print(f'  AI:    {ai_id:<15} ({ai_ms:.0f}ms)')
    print(f'  {ok}')
    print()

print('=' * 75)
print('SUMMARY')
print('=' * 75)
print(f'Agreement: {match_count}/{len(tests)} ({100*match_count//len(tests)}%)')
print(f'Avg time - Forge: {forge_total_ms/len(tests):.1f}ms, AI: {ai_total_ms/len(tests):.0f}ms')
print(f'Speed advantage: {ai_total_ms/forge_total_ms:.0f}x faster')
