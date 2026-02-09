"""
Configuration for Socratic Learner

Set your LLM provider here. For local use, set LLM_PROVIDER to "ollama".
"""

import os

# LLM Provider options:
#   "ollama"    - Local models via Ollama (FREE, runs on your machine)
#   "openai"    - OpenAI API (requires API key, costs money)
#   "anthropic" - Anthropic API (requires API key, costs money)
#   "mock"      - Fake responses for testing
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama")

# Ollama settings (for local LLM)
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")  # or phi3:mini, gemma2:2b, llama3.2:3b
OLLAMA_EXTRACT_MODEL = os.environ.get("OLLAMA_EXTRACT_MODEL", OLLAMA_MODEL)
OLLAMA_STREAM = os.environ.get("OLLAMA_STREAM", "true").lower() == "true"
OLLAMA_TIMEOUT_SEC = int(os.environ.get("OLLAMA_TIMEOUT_SEC", "300"))
OLLAMA_NUM_PREDICT = int(os.environ.get("OLLAMA_NUM_PREDICT", "900"))

# Cloud API Keys (only needed if using cloud providers)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Model selection for cloud providers
OPENAI_MODEL = "gpt-4o-mini"  # cheaper option
ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"

# Paths
SOURCES_DIR = "sources"
KNOWLEDGE_DIR = "knowledge"
EXTRACTION_CACHE_DIR = ".cache"

# Extraction settings
CHUNK_BY_SECTIONS = True  # If True, extract per section; if False, extract whole document
EXTRACTION_RETRIES = int(os.environ.get("EXTRACTION_RETRIES", "2"))
EXTRACTION_RETRY_DELAY_SEC = float(os.environ.get("EXTRACTION_RETRY_DELAY_SEC", "2.0"))

# Local model recommendations by hardware:
# 
# Minimal (4GB RAM):     gemma2:2b or tinyllama
# Standard (8GB RAM):    phi3:mini or qwen2.5:3b
# Better (16GB RAM):     llama3.2:8b or mistral:7b
# Best (32GB+ RAM):      llama3.1:70b (slow but very capable)
