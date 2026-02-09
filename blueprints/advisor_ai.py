"""
AI Advisor - Lightweight Local LLM Helper

Uses your local Ollama to answer questions about:
- Which blocks to use for your project
- How to structure your app
- What features you need

No cloud, no API keys, no overhead.
"""

import json
import urllib.request
from typing import Optional

# Ollama API
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"  # Or whatever you have installed

# System context about the blueprint system
SYSTEM_PROMPT = """You are a helpful assistant for the App Blueprint Builder system.

AVAILABLE BLOCKS (compositional code pieces):
1. auth_basic - Basic username/password authentication
   - Provides: auth, session
   - Use when: Users need to log in
   
2. storage_json - JSON file storage
   - Provides: storage, persistence
   - Use when: Simple apps, prototyping, small data
   
3. storage_sqlite - SQLite database
   - Provides: storage, database, queries
   - Use when: Need queries, relations, larger data
   
4. sync_crdt - CRDT-based sync for offline-first
   - Requires: storage
   - Provides: sync, offline, conflict_resolution
   - Use when: App needs to work offline and sync later
   
5. crud_routes - Auto-generated REST API routes
   - Requires: storage
   - Provides: api, rest, crud
   - Use when: Need standard Create/Read/Update/Delete endpoints

AVAILABLE BLUEPRINTS (app templates):
- personal-website: Portfolio, blog, contact page
- task-manager: Todo lists, projects, deadlines
- notes-app: Rich text notes, folders, search
- learning-app: Book reader, highlights, spaced repetition
- api-backend: RESTful service with auth and database

HOW TO HELP:
1. Ask what they want to build
2. Suggest which blocks they need
3. Recommend a blueprint if one fits
4. Keep answers concise and practical
5. Give specific commands they can run

Be direct and helpful. No fluff."""


def ask_ollama(prompt: str, context: str = "") -> Optional[str]:
    """Send a question to local Ollama."""
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser's question: {prompt}"
    if context:
        full_prompt = f"{SYSTEM_PROMPT}\n\nContext: {context}\n\nUser's question: {prompt}"
    
    try:
        data = json.dumps({
            "model": MODEL,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 500
            }
        }).encode()
        
        req = urllib.request.Request(
            OLLAMA_URL,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        
        response = urllib.request.urlopen(req, timeout=60)
        result = json.loads(response.read())
        return result.get("response", "No response")
        
    except urllib.error.URLError:
        return None
    except Exception as e:
        return f"Error: {e}"


def check_ollama() -> bool:
    """Check if Ollama is running."""
    try:
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5)
        return True
    except:
        return False


def interactive_chat():
    """Run an interactive chat session."""
    print("\n" + "="*60)
    print("  AI Advisor - Local LLM Helper")
    print("  Using:", MODEL)
    print("="*60)
    
    if not check_ollama():
        print("\n[!] Ollama not running. Start it with: ollama serve")
        print("    Then pull a model: ollama pull qwen2.5:7b")
        return
    
    print("\nAsk me anything about building your app!")
    print("Examples:")
    print("  - What blocks do I need for a todo app?")
    print("  - How do I add offline support?")
    print("  - What's the best blueprint for a blog?")
    print("\nType 'quit' to exit.\n")
    
    context = ""
    
    while True:
        try:
            question = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
            
        if not question:
            continue
        if question.lower() in ('quit', 'exit', 'q'):
            break
        
        print("\nThinking...", end="\r")
        response = ask_ollama(question, context)
        
        if response is None:
            print("\n[!] Couldn't reach Ollama. Is it running?")
            continue
            
        print(" " * 20, end="\r")  # Clear "Thinking..."
        print(f"\nAdvisor: {response}\n")
        
        # Keep recent context for follow-up questions
        context = f"Previous Q: {question}\nPrevious A: {response}"
    
    print("\nGoodbye!")


def quick_ask(question: str) -> str:
    """One-shot question for programmatic use."""
    if not check_ollama():
        return "Ollama not running. Start with: ollama serve"
    
    response = ask_ollama(question)
    return response or "No response"


# API for the builder server
def get_advice(project_description: str) -> dict:
    """Get block and blueprint recommendations."""
    prompt = f"""Based on this project description, recommend:
1. Which blocks to use (from the available blocks)
2. Which blueprint to start from (if any fits)
3. Key features to consider

Project: {project_description}

Be specific and actionable."""

    response = ask_ollama(prompt)
    
    if response:
        return {
            "success": True,
            "advice": response,
            "model": MODEL
        }
    else:
        return {
            "success": False,
            "error": "Ollama not available",
            "fallback": "Try: storage_sqlite + crud_routes for most apps"
        }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # One-shot mode: python advisor_ai.py "your question"
        question = " ".join(sys.argv[1:])
        print(quick_ask(question))
    else:
        # Interactive mode
        interactive_chat()
