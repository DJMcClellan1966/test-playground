"""
Knowledge Explorer

Interactive CLI for exploring extracted knowledge using Socratic dialogue.
"""

import os
import json
import re
from typing import Dict, List, Optional

import config
from llm_client import call_llm
from prompts.standard_interrogation import (
    SYSTEM_PROMPT,
    get_explain_term_prompt,
    get_explain_concept_prompt,
    get_trace_example_prompt,
    get_challenge_prompt,
    get_prerequisite_prompt,
    get_summary_prompt,
)


class KnowledgeExplorer:
    """Interactive explorer for extracted knowledge."""
    
    def __init__(self, knowledge_path: str):
        with open(knowledge_path, 'r', encoding='utf-8') as f:
            self.knowledge = json.load(f)
        
        self.full_text = self.knowledge.get("full_text", "")
        self.sections = self.knowledge.get("sections", [])
        self.history: List[Dict] = []  # Track conversation for challenges
        self.current_section_idx = 0
    
    def get_section_titles(self) -> List[str]:
        """Get list of section titles."""
        return [s["title"] for s in self.sections]
    
    def find_section(self, query: str) -> Optional[Dict]:
        """Find a section by title (partial match)."""
        query_lower = query.lower()
        for section in self.sections:
            if query_lower in section["title"].lower():
                return section
        return None
    
    def show_overview(self):
        """Show high-level overview of the content."""
        print("\n" + "="*60)
        print("📚 CONTENT OVERVIEW")
        print("="*60)
        
        print("\nSections available:")
        for i, title in enumerate(self.get_section_titles(), 1):
            print(f"  {i}. {title}")
        
        print("\n" + "-"*60)
        print("Commands:")
        print("  <number>     - View a section's extracted knowledge")
        print("  what is X    - Explain a term")
        print("  explain X    - Deep explanation of a concept")
        print("  example X    - Walk through an example")
        print("  prereqs      - What should I know before this?")
        print("  summary      - Get summaries at different levels")
        print("  source       - See original text for current section")
        print("  challenge    - Challenge the last answer")
        print("  help         - Show this help")
        print("  quit         - Exit")
        print("-"*60 + "\n")
    
    def show_section(self, section: Dict):
        """Display a section's extracted knowledge."""
        print("\n" + "="*60)
        print(f"📖 {section['title']}")
        print("="*60)
        
        extracted = section.get("extracted_knowledge", "No extraction available.")
        print(extracted)
        
        # Suggest follow-up questions
        print("\n" + "-"*60)
        print("💡 You might ask:")
        print("   - 'what is [term]' for any term you don't understand")
        print("   - 'example X' to see a worked example")
        print("   - 'challenge' if something seems wrong")
        print("-"*60 + "\n")
        
        self.current_section_idx = self.sections.index(section)
    
    def explain_term(self, term: str):
        """Explain a specific term."""
        print(f"\n🔍 Explaining: {term}\n")
        
        prompt = get_explain_term_prompt(self.full_text, term)
        response = call_llm(prompt, SYSTEM_PROMPT)
        
        print(response)
        self.history.append({"type": "explain_term", "query": term, "response": response})
    
    def explain_concept(self, concept: str):
        """Deep explanation of a concept."""
        print(f"\n🎓 Deep dive: {concept}\n")
        
        prompt = get_explain_concept_prompt(self.full_text, concept)
        response = call_llm(prompt, SYSTEM_PROMPT)
        
        print(response)
        self.history.append({"type": "explain_concept", "query": concept, "response": response})
    
    def trace_example(self, topic: str):
        """Walk through an example."""
        print(f"\n📝 Example: {topic}\n")
        
        prompt = get_trace_example_prompt(self.full_text, topic)
        response = call_llm(prompt, SYSTEM_PROMPT)
        
        print(response)
        self.history.append({"type": "example", "query": topic, "response": response})
    
    def show_prerequisites(self):
        """Show what the user should know beforehand."""
        print("\n📋 Prerequisites\n")
        
        prompt = get_prerequisite_prompt(self.full_text)
        response = call_llm(prompt, SYSTEM_PROMPT)
        
        print(response)
        self.history.append({"type": "prereqs", "response": response})
    
    def show_summaries(self):
        """Show multi-level summaries."""
        print("\n📊 Summaries at Different Levels\n")
        
        prompt = get_summary_prompt(self.full_text)
        response = call_llm(prompt, SYSTEM_PROMPT)
        
        print(response)
        self.history.append({"type": "summary", "response": response})
    
    def challenge_last(self, challenge_text: str):
        """Challenge the last answer with a follow-up."""
        if not self.history:
            print("Nothing to challenge yet. Ask a question first.")
            return
        
        last = self.history[-1]
        print(f"\n⚔️ Challenging previous answer...\n")
        
        prompt = get_challenge_prompt(
            self.full_text,
            last.get("response", ""),
            challenge_text
        )
        response = call_llm(prompt, SYSTEM_PROMPT)
        
        print(response)
        self.history.append({"type": "challenge", "query": challenge_text, "response": response})
    
    def show_source(self):
        """Show original source text for current section."""
        if self.current_section_idx < len(self.sections):
            section = self.sections[self.current_section_idx]
            print("\n" + "="*60)
            print(f"📜 SOURCE: {section['title']}")
            print("="*60)
            print(section.get("original_content", "No source available."))
        else:
            print("Select a section first.")
    
    def process_command(self, user_input: str) -> bool:
        """
        Process a user command.
        
        Returns False if user wants to quit.
        """
        cmd = user_input.strip().lower()
        
        if not cmd:
            return True
        
        # Quit commands
        if cmd in ['quit', 'exit', 'q']:
            return False
        
        # Help
        if cmd == 'help':
            self.show_overview()
            return True
        
        # Section by number
        if cmd.isdigit():
            idx = int(cmd) - 1
            if 0 <= idx < len(self.sections):
                self.show_section(self.sections[idx])
            else:
                print(f"Invalid section number. Choose 1-{len(self.sections)}")
            return True
        
        # Section by name
        section = self.find_section(cmd)
        if section:
            self.show_section(section)
            return True
        
        # "what is X" - explain term
        match = re.match(r"what(?:'s| is) (.+)", cmd)
        if match:
            self.explain_term(match.group(1))
            return True
        
        # "explain X" - deep explanation
        match = re.match(r"explain (.+)", cmd)
        if match:
            self.explain_concept(match.group(1))
            return True
        
        # "example X" - walk through example
        match = re.match(r"example(?: of)? (.+)", cmd)
        if match:
            self.trace_example(match.group(1))
            return True
        
        # Prerequisites
        if cmd in ['prereqs', 'prerequisites', 'what should i know']:
            self.show_prerequisites()
            return True
        
        # Summary
        if cmd in ['summary', 'summaries', 'summarize']:
            self.show_summaries()
            return True
        
        # Source
        if cmd == 'source':
            self.show_source()
            return True
        
        # Challenge
        if cmd.startswith('challenge'):
            rest = cmd.replace('challenge', '').strip()
            if rest:
                self.challenge_last(rest)
            else:
                print("What's your challenge? (e.g., 'challenge but what about X?')")
            return True
        
        # Default: treat as a general question
        print(f"\n💬 Answering: {user_input}\n")
        prompt = f"""Based on this authoritative text:

{self.full_text}

---

Answer this question: {user_input}

Use only information from the text. Quote relevant passages. If the answer isn't in the text, say so.
"""
        response = call_llm(prompt, SYSTEM_PROMPT)
        print(response)
        self.history.append({"type": "question", "query": user_input, "response": response})
        
        return True
    
    def run(self):
        """Run the interactive explorer."""
        print("\n" + "🎓"*20)
        print("     SOCRATIC LEARNER - Knowledge Explorer")
        print("🎓"*20)
        
        self.show_overview()
        
        while True:
            try:
                user_input = input("\n📚 Ask > ").strip()
                if not self.process_command(user_input):
                    print("\n👋 Goodbye! Keep learning.")
                    break
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Keep learning.")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")


def find_knowledge_file() -> Optional[str]:
    """Find the most recent knowledge file."""
    if not os.path.exists(config.KNOWLEDGE_DIR):
        return None
    
    files = [f for f in os.listdir(config.KNOWLEDGE_DIR) if f.endswith('_knowledge.json')]
    if not files:
        return None
    
    # Return most recently modified
    files.sort(key=lambda f: os.path.getmtime(os.path.join(config.KNOWLEDGE_DIR, f)), reverse=True)
    return os.path.join(config.KNOWLEDGE_DIR, files[0])


def main():
    """Run the explorer."""
    import sys
    
    # Find knowledge file
    if len(sys.argv) > 1:
        knowledge_path = sys.argv[1]
    else:
        knowledge_path = find_knowledge_file()
    
    if not knowledge_path or not os.path.exists(knowledge_path):
        print("No knowledge file found.")
        print("Run 'python extractor.py <source_file>' first to extract knowledge.")
        print("Or specify a knowledge file: python explorer.py knowledge/file.json")
        sys.exit(1)
    
    print(f"Loading: {knowledge_path}")
    explorer = KnowledgeExplorer(knowledge_path)
    explorer.run()


if __name__ == "__main__":
    main()
