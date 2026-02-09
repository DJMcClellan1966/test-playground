"""
Setup helper for Socratic Learner

Checks your system and helps configure the local LLM.
"""

import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from llm_client import check_ollama_status, call_llm


def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def check_system():
    """Check system readiness."""
    print_header("SOCRATIC LEARNER - Setup Check")
    
    print(f"\n📋 Configuration:")
    print(f"   LLM Provider: {config.LLM_PROVIDER}")
    
    if config.LLM_PROVIDER == "ollama":
        print(f"   Ollama Model: {config.OLLAMA_MODEL}")
        print(f"   Ollama URL:   {config.OLLAMA_BASE_URL}")
        
        print("\n🔍 Checking Ollama status...")
        status = check_ollama_status()
        
        if not status["running"]:
            print("\n❌ Ollama is NOT running!")
            print("\n   To fix this:")
            print("   1. Install Ollama:")
            print("      winget install Ollama.Ollama")
            print("   2. Start Ollama (in a separate terminal):")
            print("      ollama serve")
            print(f"   3. Download a model:")
            print(f"      ollama pull {config.OLLAMA_MODEL}")
            print("   4. Run this script again")
            return False
        
        print("   ✅ Ollama is running")
        
        if status["models"]:
            print(f"   📦 Available models: {', '.join(status['models'])}")
        else:
            print("   ⚠️  No models downloaded yet")
        
        if not status["model_available"]:
            print(f"\n❌ Model '{config.OLLAMA_MODEL}' not found!")
            print(f"\n   Download it with:")
            print(f"   ollama pull {config.OLLAMA_MODEL}")
            
            if status["models"]:
                print(f"\n   Or use an available model by editing config.py:")
                print(f"   OLLAMA_MODEL = \"{status['models'][0]}\"")
            return False
        
        print(f"   ✅ Model '{config.OLLAMA_MODEL}' is available")
        
        # Test the model
        print("\n🧪 Testing model response...")
        response = call_llm("Say 'Hello, I am working!' in exactly those words.")
        
        if "Error" in response:
            print(f"   ❌ Model test failed: {response[:100]}")
            return False
        
        print(f"   ✅ Model responded: {response[:50]}...")
        
    elif config.LLM_PROVIDER == "mock":
        print("\n   Using mock mode (no real LLM)")
        print("   This is good for testing the interface.")
        print("\n   To use a real local LLM:")
        print("   1. Install Ollama: winget install Ollama.Ollama")
        print("   2. Start it: ollama serve")
        print("   3. Download model: ollama pull phi3:mini")
        print("   4. Edit config.py: LLM_PROVIDER = 'ollama'")
        
    elif config.LLM_PROVIDER in ["openai", "anthropic"]:
        key_name = "OPENAI_API_KEY" if config.LLM_PROVIDER == "openai" else "ANTHROPIC_API_KEY"
        key_value = config.OPENAI_API_KEY if config.LLM_PROVIDER == "openai" else config.ANTHROPIC_API_KEY
        
        if not key_value:
            print(f"\n❌ {key_name} not set!")
            print(f"   Set it as an environment variable or in config.py")
            return False
        print(f"   ✅ API key configured")
    
    print_header("Setup Complete!")
    print("\n✅ You're ready to use Socratic Learner")
    print("\nNext steps:")
    print("  1. Extract knowledge: python extractor.py sources/algorithms_intro.md")
    print("  2. Explore: python explorer.py")
    print("\nOr add your own source texts to the sources/ folder.")
    
    return True


def recommend_model():
    """Recommend a model based on system resources."""
    print_header("Model Recommendations")
    
    try:
        import psutil
        ram_gb = psutil.virtual_memory().total / (1024**3)
        print(f"\n📊 Your system has ~{ram_gb:.1f} GB RAM")
        
        if ram_gb < 4:
            print("\n🔸 Recommended: gemma2:2b or tinyllama")
            print("   These are tiny but can still work for our use case")
            print("   ollama pull gemma2:2b")
        elif ram_gb < 8:
            print("\n🔸 Recommended: phi3:mini")
            print("   Excellent reasoning for its size")
            print("   ollama pull phi3:mini")
        elif ram_gb < 16:
            print("\n🔸 Recommended: qwen2.5:7b or llama3.2:3b")
            print("   Good balance of capability and speed")
            print("   ollama pull qwen2.5:7b")
        else:
            print("\n🔸 Recommended: llama3.1:8b or mistral:7b")
            print("   High quality responses")
            print("   ollama pull llama3.1:8b")
            
    except ImportError:
        print("\n(Install psutil for RAM detection: pip install psutil)")
        print("\nGeneral recommendations:")
        print("  4GB RAM:  ollama pull gemma2:2b")
        print("  8GB RAM:  ollama pull phi3:mini")
        print("  16GB RAM: ollama pull qwen2.5:7b")
        print("  32GB RAM: ollama pull llama3.1:8b")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--recommend":
        recommend_model()
    else:
        check_system()
