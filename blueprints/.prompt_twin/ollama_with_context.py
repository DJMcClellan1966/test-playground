#!/usr/bin/env python3
"""
Ollama wrapper that auto-injects your prompt twin context.
Usage: python ollama_with_context.py "your prompt here"
"""
import sys
import json
import urllib.request

CONTEXT = """
## Developer Profile
Technologies: Machine Learning, OpenAI, Auth, Flask, SQLite
Languages: .py(926), .cs(162), .js(116)
Project Types: ML/AI Project, API Service, Web App
GitHub: @DJMcClellan1966 (64 repos)
GitHub Languages: Python(14), HTML(7), C#(7)
Commit Style: add new features incrementally

## Preferences
- Local-first (Ollama, SQLite)
- Practical working code over theory
- Full-stack Python + .NET
- Interested in ML/AI, information theory
"""

def query_ollama(prompt, model="qwen2.5:7b"):
    """Query Ollama with auto-injected context"""
    full_prompt = f"{CONTEXT}\n\nUser request: {prompt}"
    
    data = json.dumps({
        "model": model,
        "prompt": full_prompt,
        "stream": False
    }).encode()
    
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    
    resp = urllib.request.urlopen(req, timeout=120)
    result = json.loads(resp.read())
    return result.get("response", "")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ollama_with_context.py \"your prompt\"")
        sys.exit(1)
    
    prompt = " ".join(sys.argv[1:])
    print(query_ollama(prompt))
