"""
LLM Client

Handles communication with different LLM providers, including local models via Ollama.
"""

import config


def call_llm(prompt: str, system_prompt: str = "", model_override: str | None = None) -> str:
    """
    Send a prompt to the LLM and return the response.
    
    Args:
        prompt: The user/extraction prompt
        system_prompt: Optional system prompt for context
        
    Returns:
        The LLM's response text
    """
    provider = config.LLM_PROVIDER.lower()
    
    if provider == "mock":
        return _mock_response(prompt)
    elif provider == "ollama":
        return _call_ollama(prompt, system_prompt, model_override)
    elif provider == "openai":
        return _call_openai(prompt, system_prompt)
    elif provider == "anthropic":
        return _call_anthropic(prompt, system_prompt)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def _call_ollama(prompt: str, system_prompt: str, model_override: str | None) -> str:
    """
    Call a local LLM via Ollama.
    
    Ollama must be running: `ollama serve`
    Model must be downloaded: `ollama pull phi3:mini`
    """
    import urllib.request
    import json
    
    url = f"{config.OLLAMA_BASE_URL}/api/generate"
    
    # Combine system prompt and user prompt
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n---\n\n{prompt}"
    
    model_name = model_override or config.OLLAMA_MODEL
    data = {
        "model": model_name,
        "prompt": full_prompt,
        "stream": config.OLLAMA_STREAM,
        "options": {
            "temperature": 0.3,  # Lower = more focused/deterministic
            "num_predict": config.OLLAMA_NUM_PREDICT,
        }
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        # Local LLMs can be slow - configurable timeout per request
        with urllib.request.urlopen(req, timeout=config.OLLAMA_TIMEOUT_SEC) as response:
            if not config.OLLAMA_STREAM:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", "No response from model")

            chunks = []
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "response" in payload:
                    chunks.append(payload["response"])
                if payload.get("done") is True:
                    break
            return "".join(chunks) or "No response from model"
            
    except urllib.error.URLError as e:
        return f"""Error connecting to Ollama: {e}

Make sure Ollama is running:
1. Install Ollama: winget install Ollama.Ollama
2. Start it: ollama serve
3. Download a model: ollama pull {config.OLLAMA_MODEL}
4. Try again

Or set LLM_PROVIDER=mock in config.py to use mock responses."""
    
    except Exception as e:
        return f"Error calling Ollama: {e}"


def check_ollama_status() -> dict:
    """Check if Ollama is running and what models are available."""
    import urllib.request
    import json
    
    status = {
        "running": False,
        "models": [],
        "selected_model": config.OLLAMA_MODEL,
        "model_available": False
    }
    
    try:
        # Check if Ollama is running
        url = f"{config.OLLAMA_BASE_URL}/api/tags"
        with urllib.request.urlopen(url, timeout=5) as response:
            result = json.loads(response.read().decode('utf-8'))
            status["running"] = True
            status["models"] = [m["name"] for m in result.get("models", [])]
            status["model_available"] = config.OLLAMA_MODEL in status["models"]
    except:
        pass
    
    return status


def _mock_response(prompt: str) -> str:
    """
    Return a mock response for testing without API access.
    This simulates what the extraction would look like.
    """
    if "Extract the following" in prompt:
        return """## Overview
This section introduces the concept of an algorithm - a precise, finite procedure for solving problems. It uses Euclid's algorithm for finding the greatest common divisor as the primary example.

## Prerequisites
- Basic arithmetic (addition, subtraction, multiplication, division)
- Understanding of integers and remainders
- Concept of divisibility (what it means for one number to divide another)

## Key Terms
- **Algorithm**: "A finite sequence of well-defined instructions for solving a class of problems or performing a computation"
- **Finiteness**: An algorithm must always terminate after a finite number of steps
- **Definiteness**: Each step must be precisely defined with unambiguous actions
- **Effectiveness**: Operations must be basic enough to be done by hand with pencil and paper
- **GCD (Greatest Common Divisor)**: The largest positive integer that divides both numbers without remainder

## Main Claims
1. An algorithm must satisfy five properties: finiteness, definiteness, input, output, and effectiveness
2. Algorithms are abstract concepts; programs are concrete implementations
3. Euclid's algorithm correctly finds the GCD because gcd(m,n) = gcd(n, m mod n)

## Key Steps/Process
Euclid's Algorithm:
1. E1 - Divide m by n, let r be the remainder
2. E2 - If r = 0, n is the GCD (terminate)
3. E3 - Set m ← n, n ← r, return to step 1

## Concrete Examples
- gcd(544, 119): Traced through 5 iterations to find gcd = 17
  - Shows how m and n values change each step
  - Verification: 544 = 17 × 32 and 119 = 17 × 7

## Common Pitfalls
- Confusing "algorithm" with "program" - algorithms are abstract, programs are implementations
- Confusing "effective" with "efficient" - effective means doable at all, not necessarily fast
- Assuming all procedures are algorithms - infinite loops disqualify a procedure

## Connections
- Mathematical proofs (the theorem underlying Euclid's algorithm)
- Fibonacci numbers (relate to worst-case analysis)
- Number theory (divisibility, remainders)

## One-Sentence Summary
An algorithm is a finite, precise procedure that always terminates with a correct answer, exemplified by Euclid's 2300-year-old method for finding the greatest common divisor.
"""
    
    elif "explain" in prompt.lower() and "term" in prompt.lower():
        return """**Simple definition**: An algorithm is a recipe - a step-by-step procedure that always works and always finishes.

**Why it matters**: Without a precise definition of algorithm, we can't distinguish between procedures that are guaranteed to work and those that might run forever or give wrong answers.

**Concrete example**: Euclid's algorithm for finding the GCD is an algorithm because:
- It always terminates (the remainder keeps getting smaller)
- Each step is precisely defined
- It works for any valid input

**What it's NOT**:
- It's not a program (that's an implementation)
- It's not a heuristic (which might not always work)
- It's not a procedure that could loop forever

**From the text**: "An algorithm is a finite sequence of well-defined instructions for solving a class of problems or performing a computation."
"""
    
    else:
        return "This is a mock response. Set LLM_PROVIDER to 'openai' or 'anthropic' with valid API keys for real responses."


def _call_openai(prompt: str, system_prompt: str) -> str:
    """Call OpenAI API."""
    try:
        from openai import OpenAI
    except ImportError:
        return "Error: openai package not installed. Run: pip install openai"
    
    if not config.OPENAI_API_KEY:
        return "Error: OPENAI_API_KEY not set"
    
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=messages
    )
    
    return response.choices[0].message.content


def _call_anthropic(prompt: str, system_prompt: str) -> str:
    """Call Anthropic API."""
    try:
        from anthropic import Anthropic
    except ImportError:
        return "Error: anthropic package not installed. Run: pip install anthropic"
    
    if not config.ANTHROPIC_API_KEY:
        return "Error: ANTHROPIC_API_KEY not set"
    
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    
    message = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=4096,
        system=system_prompt if system_prompt else "You are a helpful assistant.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return message.content[0].text
