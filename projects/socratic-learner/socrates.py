"""
Socrates - The Questioning Guide

A Socratic dialogue partner that helps inexperienced learners:
1. Identify flawed assumptions in their questions
2. Ask clarifying questions to expose misconceptions
3. Guide toward better questions
4. Never just gives answers - leads to discovery

The key insight: an inexperienced person doesn't know what they don't know.
Their questions may be based on fundamentally wrong assumptions.
Socrates helps them discover this through dialogue.
"""

import json
import os
from pathlib import Path
from typing import Optional, List, Dict

import config
from llm_client import call_llm


# The Socratic System Prompt - this is the heart of the guide
SOCRATES_SYSTEM_PROMPT = """You are Socrates, a wise teacher who helps learners through questioning.

RULES:
- Never give direct answers immediately
- Ask clarifying questions to expose flawed assumptions
- Be patient and encouraging
- Keep responses brief (2-4 sentences)

Common flaws to watch for:
- Confusing "effective" (doable) with "efficient" (fast)
- Confusing "algorithm" with "program"
- Wrong cause-and-effect assumptions
"""


QUESTION_ANALYSIS_PROMPT = """You are Socrates helping a learner.

LEARNER ASKED: {question}

RELEVANT CONTEXT FROM AUTHORITATIVE TEXT:
{knowledge_context}

COMMON MISCONCEPTIONS TO WATCH FOR:
- "Effective" means doable (can be done by hand) - NOT about speed!
- "Efficient" means fast - this is about speed
- Algorithm is abstract; program is concrete implementation
- All algorithms must terminate; infinite loops are not algorithms

If the learner confuses these terms, gently ask: "When you say [term], what exactly do you mean by that?"

Respond briefly as Socrates (2-4 sentences). Ask questions, don't lecture.
"""


class Socrates:
    """
    A Socratic dialogue partner that guides learners through questioning.
    """
    
    def __init__(self, knowledge_path: Optional[str] = None):
        """
        Initialize Socrates with optional knowledge base.
        
        Args:
            knowledge_path: Path to extracted knowledge JSON file
        """
        self.knowledge = None
        self.dialogue_history: List[Dict] = []
        
        if knowledge_path and os.path.exists(knowledge_path):
            with open(knowledge_path, 'r', encoding='utf-8') as f:
                self.knowledge = json.load(f)
            print(f"📚 Socrates has studied: {knowledge_path}")
        else:
            print("⚠️  Socrates has no knowledge base loaded")
            print("   He can still help, but with less context")
    
    def _find_relevant_knowledge(self, question: str) -> str:
        """
        Find sections of knowledge relevant to the question.
        
        Uses keyword matching for now - could be improved with embeddings.
        """
        if not self.knowledge:
            return "No authoritative text available."
        
        question_lower = question.lower()
        relevant_sections = []
        
        # Score each section by keyword overlap
        for section in self.knowledge.get("sections", []):
            title = section.get("title", "").lower()
            content = section.get("original_content", "").lower()
            extracted = section.get("extracted_knowledge", "").lower()
            
            # Simple scoring: count keyword matches
            score = 0
            for word in question_lower.split():
                if len(word) > 3:  # Skip short words
                    if word in title:
                        score += 3
                    if word in extracted:
                        score += 2
                    if word in content:
                        score += 1
            
            if score > 0:
                relevant_sections.append((score, section))
        
        # Sort by relevance and take top 3
        relevant_sections.sort(key=lambda x: x[0], reverse=True)
        top_sections = relevant_sections[:3]
        
        if not top_sections:
            return "No directly relevant sections found in the authoritative text."
        
        # Build context string - keep it short for local LLMs
        context_parts = []
        for score, section in top_sections[:2]:  # Only top 2 sections
            # Use just the overview and key terms, not full extraction
            extracted = section.get('extracted_knowledge', '')
            # Take first 500 chars max
            context_parts.append(f"### {section['title']}\n{extracted[:500]}")
        
        return "\n\n".join(context_parts)
    
    def respond(self, question: str) -> str:
        """
        Respond to a learner's question using the Socratic method.
        
        Args:
            question: The learner's question
            
        Returns:
            Socrates' response (usually a clarifying question or guided exploration)
        """
        # Find relevant knowledge
        knowledge_context = self._find_relevant_knowledge(question)
        
        # Build the analysis prompt
        prompt = QUESTION_ANALYSIS_PROMPT.format(
            question=question,
            knowledge_context=knowledge_context
        )
        
        # Get Socrates' response
        response = call_llm(prompt, SOCRATES_SYSTEM_PROMPT)
        
        # Store in dialogue history
        self.dialogue_history.append({
            "role": "learner",
            "content": question
        })
        self.dialogue_history.append({
            "role": "socrates",
            "content": response
        })
        
        return response
    
    def continue_dialogue(self, response: str) -> str:
        """
        Continue an ongoing dialogue after the learner responds to Socrates.
        
        Args:
            response: The learner's response to Socrates' question
            
        Returns:
            Socrates' next response
        """
        # Build dialogue context
        dialogue_context = ""
        for entry in self.dialogue_history[-6:]:  # Last 3 exchanges
            role = "Learner" if entry["role"] == "learner" else "Socrates"
            dialogue_context += f"{role}: {entry['content']}\n\n"
        
        prompt = f"""Continue this Socratic dialogue. The learner has responded to your question.

PREVIOUS DIALOGUE:
{dialogue_context}

LEARNER'S NEW RESPONSE: {response}

Continue guiding them toward understanding. If they've gained insight, 
acknowledge it and go deeper. If they're still confused, try a different approach.
Remember: guide through questions, don't lecture.
"""
        
        socrates_response = call_llm(prompt, SOCRATES_SYSTEM_PROMPT)
        
        # Update history
        self.dialogue_history.append({
            "role": "learner", 
            "content": response
        })
        self.dialogue_history.append({
            "role": "socrates",
            "content": socrates_response
        })
        
        return socrates_response
    
    def reset_dialogue(self):
        """Clear the dialogue history to start fresh."""
        self.dialogue_history = []
        print("🔄 Dialogue reset. Ask a new question!")
    
    def give_hint(self) -> str:
        """
        Give a hint based on the current dialogue without fully revealing the answer.
        """
        if not self.dialogue_history:
            return "Ask a question first, then I can give you a hint!"
        
        # Get the last question
        last_question = None
        for entry in reversed(self.dialogue_history):
            if entry["role"] == "learner":
                last_question = entry["content"]
                break
        
        if not last_question:
            return "I don't see a question to hint about."
        
        knowledge_context = self._find_relevant_knowledge(last_question)
        
        prompt = f"""The learner asked: {last_question}

Based on this context from the authoritative text:
{knowledge_context}

Give ONE brief hint (1-2 sentences) that points them in the right direction 
without fully revealing the answer. Start with "Consider..." or "Think about..."
"""
        
        return call_llm(prompt, "You are a helpful tutor giving gentle hints.")
    
    def reveal_answer(self) -> str:
        """
        Directly quote the authoritative text related to the current question.
        This breaks the Socratic method but is available when truly stuck.
        """
        if not self.dialogue_history:
            return "Ask a question first!"
        
        # Get the last question
        last_question = None
        for entry in reversed(self.dialogue_history):
            if entry["role"] == "learner":
                last_question = entry["content"]
                break
        
        if not last_question:
            return "I don't see a question to answer."
        
        knowledge_context = self._find_relevant_knowledge(last_question)
        
        return f"From the authoritative text:\n\n{knowledge_context}"


def run_interactive_session(knowledge_path: Optional[str] = None):
    """
    Run an interactive Socratic dialogue session.
    """
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🏛️  SOCRATES - Your Guide to Understanding                    ║
║                                                                  ║
║   I won't just give you answers. I'll help you discover them.   ║
║   Ask me anything - but be prepared for questions in return!    ║
║                                                                  ║
║   Commands:                                                      ║
║     /hint   - Get a gentle nudge in the right direction         ║
║     /reveal - Show what the authoritative text says (gives up!) ║
║     /reset  - Start a new dialogue                               ║
║     /quit   - Exit                                               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    # Try to find default knowledge file
    if knowledge_path is None:
        default_path = Path("knowledge")
        if default_path.exists():
            knowledge_files = list(default_path.glob("*_knowledge.json"))
            if knowledge_files:
                knowledge_path = str(knowledge_files[0])
                print(f"📖 Found knowledge base: {knowledge_path}")
    
    socrates = Socrates(knowledge_path)
    print()
    
    while True:
        try:
            user_input = input("🧑 You > ").strip()
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\n\n👋 Until we meet again, seeker of wisdom!")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() == "/quit":
            print("\n👋 Until we meet again, seeker of wisdom!")
            break
        
        if user_input.lower() == "/reset":
            socrates.reset_dialogue()
            continue
        
        if user_input.lower() == "/hint":
            print("\n💡 Let me give you a hint from the text...")
            hint = socrates.give_hint()
            print(f"\n📜 {hint}\n")
            continue
        
        if user_input.lower() == "/reveal":
            print("\n🎓 Here's what the authoritative text says...")
            reveal = socrates.reveal_answer()
            print(f"\n📜 {reveal}\n")
            continue
        
        # Get Socrates' response
        print()
        print("🏛️ Socrates is thinking...")
        
        if len(socrates.dialogue_history) == 0:
            response = socrates.respond(user_input)
        else:
            response = socrates.continue_dialogue(user_input)
        
        print()
        print(f"🏛️ Socrates > {response}")
        print()


def main():
    """Main entry point."""
    import sys
    
    knowledge_path = None
    if len(sys.argv) > 1:
        knowledge_path = sys.argv[1]
    
    run_interactive_session(knowledge_path)


if __name__ == "__main__":
    main()
