"""Quick test of single section extraction"""

import config
from llm_client import call_llm
from prompts.standard_interrogation import get_extraction_prompt, SYSTEM_PROMPT

# Simple test text
test_text = """
# What is an Algorithm?

An **algorithm** is a finite sequence of well-defined instructions for solving 
a class of problems or performing a computation.

For a procedure to qualify as an algorithm, it must satisfy five properties:
1. **Finiteness**: Must terminate after finite steps
2. **Definiteness**: Each step precisely defined
3. **Input**: Zero or more inputs
4. **Output**: One or more outputs
5. **Effectiveness**: Operations can be done by hand
"""

print(f"Using provider: {config.LLM_PROVIDER}")
print(f"Using model: {config.OLLAMA_MODEL}")
print()
print("Sending request to LLM...")
print()

# Use a simplified prompt for faster testing
simple_prompt = f"""Analyze this text and provide:
1. One-sentence summary
2. Key terms (2-3 with definitions)
3. Main point

TEXT:
{test_text}

Keep your response concise (under 200 words).
"""

result = call_llm(simple_prompt, "You are a helpful assistant that extracts key information from educational texts.")
print("=== LLM Response ===")
print(result)
