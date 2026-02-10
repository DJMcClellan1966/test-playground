"""Extract VS Code Copilot chat history"""
import os
import json
import sqlite3
from pathlib import Path

out_path = Path(__file__).parent / 'cursor_data_sample.txt'

# VS Code global state database
code_global_db = Path(os.environ['APPDATA']) / 'Code/User/globalStorage/state.vscdb'

with open(out_path, 'w', encoding='utf-8') as f:
    conn = sqlite3.connect(str(code_global_db))
    cursor = conn.cursor()
    
    # Get the chat session store
    cursor.execute("SELECT key, value FROM ItemTable WHERE key = 'chat.ChatSessionStore.index'")
    row = cursor.fetchone()
    
    if row:
        key, value = row
        f.write(f'=== {key} ===\n')
        f.write(f'Size: {len(value) if value else 0} bytes\n\n')
        
        if value:
            try:
                data = json.loads(value)
                f.write(f'Type: {type(data).__name__}\n')
                if isinstance(data, dict):
                    f.write(f'Keys: {list(data.keys())}\n')
                    f.write(f'\nFull data:\n')
                    f.write(json.dumps(data, indent=2)[:10000])
                elif isinstance(data, list):
                    f.write(f'Items: {len(data)}\n')
                    f.write(f'\nFirst 3 items:\n')
                    for i, item in enumerate(data[:3]):
                        f.write(f'\n--- Item {i+1} ---\n')
                        f.write(json.dumps(item, indent=2)[:3000])
            except Exception as e:
                f.write(f'Error parsing: {e}\n')
                f.write(f'\nRaw value (first 5000 chars):\n')
                if isinstance(value, bytes):
                    f.write(value.decode('utf-8', errors='replace')[:5000])
                else:
                    f.write(str(value)[:5000])
    else:
        f.write('chat.ChatSessionStore.index not found\n')
    
    # Also check GitHub.copilot-chat
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'GitHub.copilot-chat'")
    row = cursor.fetchone()
    if row and row[0]:
        f.write(f'\n\n=== GitHub.copilot-chat ===\n')
        try:
            data = json.loads(row[0])
            f.write(json.dumps(data, indent=2)[:5000])
        except:
            f.write(str(row[0])[:5000])
    
    conn.close()

print(f'Wrote to: {out_path}')
