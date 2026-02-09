"""
Blueprint Generator - Create custom blueprints through dialogue.

The revolutionary piece: Instead of picking from templates, users describe
what they want in natural language. The system synthesizes a completely
custom blueprint by understanding patterns across existing blueprints.

This enables:
- Blueprints for apps that don't exist in the library
- Personalized specs that match YOUR context exactly
- Hybrid apps that combine features from multiple blueprints
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add socratic-learner path for LLM imports
_socratic_path = Path(__file__).parent.parent / "projects" / "socratic-learner"
if _socratic_path.exists():
    sys.path.insert(0, str(_socratic_path))

try:
    import config  # type: ignore
    from llm_client import call_llm  # type: ignore
    LLM_AVAILABLE = True
except ImportError:
    config = None
    call_llm = None
    LLM_AVAILABLE = False


BLUEPRINTS_DIR = Path(__file__).parent.parent.parent / "blueprints"
CUSTOM_BLUEPRINTS_DIR = BLUEPRINTS_DIR / "custom"


# ============================================================================
# SYSTEM PROMPTS
# ============================================================================

BLUEPRINT_SYNTHESIS_SYSTEM = """You are an expert software architect who creates detailed app blueprints.

You will be given:
1. A conversation where a user described what they want to build
2. Example blueprints showing the expected format and depth

Your job: Synthesize a complete, custom blueprint for their specific app.

RULES:
- Follow the blueprint template structure exactly
- Be specific to their use case, not generic
- Include features they mentioned AND obvious ones they'd expect
- Data model should have all fields needed for the features
- File structure should match the recommended stack
- Include realistic pitfalls for their specific app type
- MVP scope should be genuinely minimal but useful

OUTPUT: A complete markdown blueprint document."""


BLUEPRINT_TEMPLATE = """# {title} Blueprint

> {tagline}

---

## Core Purpose

{core_purpose}

---

## User Types

| User | Goal | Key Actions |
|------|------|-------------|
{user_types}

---

## Feature Categories

{feature_categories}

---

## User Flows

{user_flows}

---

## Screens/Pages

| Screen | Purpose | Key Components |
|--------|---------|----------------|
{screens}

---

## Data Model

{data_model}

---

## Technical Stack (Recommended)

| Concern | Recommendation | Why |
|---------|----------------|-----|
{tech_stack}

---

## MVP Scope

**Must have for v1:**
{mvp_scope}

**Explicitly NOT in MVP:**
{not_mvp}

---

## Full Vision

{full_vision}

---

## File Structure

```
{file_structure}
```

---

## Common Pitfalls

{pitfalls}

---

## Implementation Order

{implementation_order}

---

## Appendix: Code Patterns

{code_patterns}
"""


SYNTHESIS_PROMPT = """Based on this conversation, create a complete app blueprint.

## CONVERSATION:
{dialogue}

## EXAMPLE BLUEPRINT (for format reference):
{example_blueprint}

## REQUIREMENTS:
1. Create a blueprint for exactly what the user described
2. Follow the same structure as the example
3. Be specific to their needs - this is THEIR custom app, not a template
4. Include all sections: Core Purpose, User Types, Feature Categories, User Flows, Screens, Data Model, Tech Stack, MVP Scope, Full Vision, File Structure, Common Pitfalls, Implementation Order, Appendix
5. For Data Model, use the format:
   ### EntityName
   ```
   id: string (uuid)
   field: type
   ```
6. For File Structure, use a tree format starting with the project name

Generate the complete blueprint in markdown format:"""


# ============================================================================
# DIALOGUE COLLECTION
# ============================================================================

DISCOVERY_QUESTIONS = [
    {
        "id": "what",
        "question": "What do you want to build? Describe it in a sentence or two.",
        "followup": "What's the ONE thing this app must do really well?"
    },
    {
        "id": "who",
        "question": "Who will use this? (yourself, specific group, general public)",
        "followup": "What problem does it solve for them?"
    },
    {
        "id": "uniqueness",
        "question": "How is this different from existing apps you've tried?",
        "followup": "What frustrated you about those apps?"
    },
    {
        "id": "data",
        "question": "What data will the app manage? (e.g., notes, tasks, files, records)",
        "followup": "How should that data be organized?"
    },
    {
        "id": "workflow",
        "question": "Walk me through a typical session using this app.",
        "followup": "What's the most common action you'd take?"
    },
    {
        "id": "constraints",
        "question": "Any technical constraints? (offline needed, specific platform, integration)",
        "followup": "What's your experience level with coding?"
    },
    {
        "id": "mvp",
        "question": "If you could only have 3 features, what would they be?",
        "followup": "What would make you say 'this is working' after a week of use?"
    }
]


class BlueprintGenerator:
    """Generate custom blueprints through Socratic dialogue."""
    
    def __init__(self):
        self.dialogue: List[Dict] = []
        self.similar_blueprints: List[str] = []
        self.current_question_idx = 0
        
        # Create custom blueprints directory
        CUSTOM_BLUEPRINTS_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_example_blueprints(self, limit: int = 2) -> str:
        """Load example blueprints for few-shot learning."""
        examples = []
        
        for md_file in sorted(BLUEPRINTS_DIR.glob("*.md"))[:limit + 2]:
            if md_file.name in ("README.md", "GUIDE-building-without-ai.md"):
                continue
            if len(examples) >= limit:
                break
            
            content = md_file.read_text(encoding="utf-8")
            # Truncate to key sections for context window
            lines = content.split("\n")
            truncated = "\n".join(lines[:300])  # First 300 lines
            examples.append(f"### Example: {md_file.stem}\n\n{truncated}\n...(truncated)")
        
        return "\n\n---\n\n".join(examples)
    
    def _find_similar_blueprints(self, description: str) -> List[str]:
        """Find blueprints that might be relevant based on keywords."""
        keywords = description.lower().split()
        matches = []
        
        for md_file in BLUEPRINTS_DIR.glob("*.md"):
            if md_file.name in ("README.md", "GUIDE-building-without-ai.md"):
                continue
            
            content = md_file.read_text(encoding="utf-8").lower()
            score = sum(1 for kw in keywords if len(kw) > 3 and kw in content)
            
            if score > 0:
                matches.append((score, md_file.stem))
        
        matches.sort(reverse=True)
        return [name for _, name in matches[:3]]
    
    def get_next_question(self) -> Optional[str]:
        """Get the next discovery question."""
        if self.current_question_idx >= len(DISCOVERY_QUESTIONS):
            return None
        
        q = DISCOVERY_QUESTIONS[self.current_question_idx]
        return q["question"]
    
    def process_answer(self, answer: str) -> str:
        """Process user's answer and return followup or next question."""
        if self.current_question_idx >= len(DISCOVERY_QUESTIONS):
            return "I have enough information to generate your blueprint!"
        
        q = DISCOVERY_QUESTIONS[self.current_question_idx]
        
        # Store the answer
        self.dialogue.append({
            "question": q["question"],
            "answer": answer
        })
        
        # Find similar blueprints after first answer
        if self.current_question_idx == 0:
            self.similar_blueprints = self._find_similar_blueprints(answer)
            if self.similar_blueprints:
                print(f"\n   (Detected similar patterns: {', '.join(self.similar_blueprints)})")
        
        self.current_question_idx += 1
        
        # Return next question or completion message  
        next_q = self.get_next_question()
        if next_q:
            return next_q
        else:
            return "I have enough information! Generating your custom blueprint..."
    
    def generate_blueprint(self, app_name: str) -> str:
        """Generate a complete blueprint from collected dialogue."""
        if len(self.dialogue) < 3:
            raise ValueError("Need more dialogue before generating. Answer at least 3 questions.")
        
        # Format dialogue for prompt
        dialogue_text = ""
        for entry in self.dialogue:
            dialogue_text += f"Q: {entry['question']}\nA: {entry['answer']}\n\n"
        
        # Get example blueprint for format reference
        example = self._load_example_blueprints(limit=1)
        
        # Generate with LLM
        print("\n🧠 Synthesizing your custom blueprint...")
        print("   (This may take 30-60 seconds with local LLM)\n")
        
        prompt = SYNTHESIS_PROMPT.format(
            dialogue=dialogue_text,
            example_blueprint=example
        )
        
        # Use larger num_predict for blueprint generation
        if config is not None:
            original_predict = config.OLLAMA_NUM_PREDICT
            config.OLLAMA_NUM_PREDICT = 4000  # Need more tokens for full blueprint
        
        try:
            blueprint_content = call_llm(prompt, BLUEPRINT_SYNTHESIS_SYSTEM)
        finally:
            if config is not None:
                config.OLLAMA_NUM_PREDICT = original_predict
        
        # Save the blueprint
        safe_name = app_name.lower().replace(" ", "-")
        output_path = CUSTOM_BLUEPRINTS_DIR / f"{safe_name}.md"
        
        # Add generation metadata
        metadata = f"""<!--
Generated: {datetime.now().isoformat()}
Based on dialogue with {len(self.dialogue)} Q&A pairs
Similar to: {', '.join(self.similar_blueprints) or 'novel concept'}
-->

"""
        full_content = metadata + blueprint_content
        output_path.write_text(full_content, encoding="utf-8")
        
        print(f"✅ Blueprint saved to: {output_path}")
        return str(output_path)
    
    def get_dialogue_summary(self) -> str:
        """Get a summary of collected dialogue."""
        lines = []
        for i, entry in enumerate(self.dialogue, 1):
            lines.append(f"{i}. {entry['question']}")
            lines.append(f"   → {entry['answer'][:100]}...")
        return "\n".join(lines)


# ============================================================================
# CLI
# ============================================================================

def run_cli():
    """Run the blueprint generator as an interactive CLI."""
    if not LLM_AVAILABLE:
        print("\n❌ LLM client not available.")
        print("   This tool requires the socratic-learner LLM client.")
        print("   Make sure Ollama is running and try again.")
        return
    
    print("\n" + "=" * 60)
    print("   🎨 CUSTOM BLUEPRINT GENERATOR")
    print("   Describe your app, get a complete specification")
    print("=" * 60)
    print("\nI'll ask you some questions to understand what you want to build.")
    print("Then I'll generate a complete blueprint customized for YOUR app.\n")
    print("Type 'quit' at any time to exit.\n")
    
    generator = BlueprintGenerator()
    
    # Run through discovery questions
    question = generator.get_next_question()
    
    while question:
        print(f"📝 {question}")
        try:
            answer = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye!")
            return
        
        if answer.lower() == 'quit':
            print("\nGoodbye!")
            return
        
        if not answer:
            print("   (Please provide an answer)")
            continue
        
        response = generator.process_answer(answer)
        print(f"\n{response}\n")
        
        question = generator.get_next_question()
    
    # Generate the blueprint
    print("\n" + "-" * 40)
    print("Now let's name your app.\n")
    
    app_name = input("App name: ").strip()
    if not app_name:
        app_name = "MyCustomApp"
    
    try:
        output_path = generator.generate_blueprint(app_name)
        print(f"\n🚀 Next steps:")
        print(f"   1. Review your blueprint: {output_path}")
        print(f"   2. Customize any sections that need adjusting")
        print(f"   3. Generate code: python scaffold.py custom/{app_name.lower().replace(' ', '-')} --generate")
        print(f"\n📖 Your dialogue summary:")
        print(generator.get_dialogue_summary())
        
    except Exception as e:
        print(f"\n❌ Error generating blueprint: {e}")
        print("   Try again or check that Ollama is running.")


if __name__ == "__main__":
    run_cli()
