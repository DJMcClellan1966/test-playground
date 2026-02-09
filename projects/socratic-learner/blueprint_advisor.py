"""
Blueprint Advisor - Socratic guidance for app blueprint selection and customization.

Uses the Socratic method to help users:
1. Discover which blueprint fits their needs
2. Identify which features matter for their context
3. Make informed technical stack decisions
4. Scope their MVP appropriately

Rather than telling users what to build, we ask questions that
lead them to discover the right answers themselves.
"""

import json
import os
from pathlib import Path
from typing import Optional, List, Dict

import config
from llm_client import call_llm


# Path to blueprints directory (relative to this file's parent)
BLUEPRINTS_DIR = Path(__file__).parent.parent.parent / "blueprints"


# ============================================================================
# SOCRATIC SYSTEM PROMPTS FOR BLUEPRINT GUIDANCE
# ============================================================================

ADVISOR_SYSTEM_PROMPT = """You are a Socratic advisor helping someone decide what app to build.

RULES:
- Never prescribe solutions directly
- Ask clarifying questions to help them discover requirements
- One question at a time (keep focused)
- Be encouraging but probe assumptions
- Keep responses to 2-4 sentences

Your goal: Help them realize what they actually need vs what they think they want.
Common discoveries:
- They need something simpler than they imagined
- A feature they dismissed is actually critical
- Their "unique" need is a standard pattern
"""


BLUEPRINT_DISCOVERY_PROMPT = """You are helping someone find the right app blueprint.

AVAILABLE BLUEPRINTS:
{blueprint_summaries}

USER'S DESCRIPTION: {description}

DIALOGUE SO FAR:
{dialogue_history}

Ask ONE clarifying question to narrow down which blueprint fits best.
Focus on discovering:
- What users will primarily DO (consume vs create content)
- Whether it's for themselves or others
- What makes it "done" (what success looks like)

Keep it brief (2-3 sentences). Don't list blueprints yet - ask to understand first.
"""


FEATURE_DISCOVERY_PROMPT = """You are helping someone customize features for their {blueprint_name}.

AVAILABLE FEATURES IN THIS BLUEPRINT:
{features}

THEIR STATED GOAL: {goal}

DIALOGUE SO FAR:
{dialogue_history}

Ask ONE question to help them discover which features truly matter.
Probe for:
- Hidden requirements they haven't mentioned
- Features they dismissed that might be essential
- Over-engineering tendencies (wanting everything)

Keep it brief (2-3 sentences).
"""


MVP_SCOPING_PROMPT = """You are helping someone scope their MVP for a {blueprint_name}.

THEIR CHOSEN FEATURES:
{chosen_features}

DIALOGUE SO FAR:
{dialogue_history}

Ask ONE question to help them identify the absolute minimum needed.
Probe for:
- Which feature proves the core value proposition?
- What can they learn with the least code?
- Are they building for feedback or for completion?

Keep it brief (2-3 sentences).
"""


STACK_ADVISOR_PROMPT = """You are helping someone choose a technical stack for their {blueprint_name}.

THEIR EXPERIENCE: {experience}
THEIR CONSTRAINTS: {constraints}

RECOMMENDED OPTIONS:
{stack_options}

DIALOGUE SO FAR:
{dialogue_history}

Ask ONE question to guide them toward the right choice.
Consider:
- What they already know (leverage existing skills)
- Deployment constraints
- Long-term maintenance

Keep it brief (2-3 sentences).
"""


class BlueprintAdvisor:
    """
    A Socratic advisor for app blueprint selection and customization.
    """
    
    def __init__(self):
        """Initialize the advisor and load available blueprints."""
        self.blueprints = self._load_blueprints()
        self.dialogue_history: List[Dict] = []
        self.current_mode = "discovery"  # discovery, features, mvp, stack
        self.selected_blueprint: Optional[str] = None
        self.user_context: Dict = {}
        
        print(f"🎯 Blueprint Advisor ready")
        print(f"   {len(self.blueprints)} blueprints available")
    
    def _load_blueprints(self) -> Dict[str, Dict]:
        """Load and parse all available blueprints."""
        blueprints = {}
        
        if not BLUEPRINTS_DIR.exists():
            print(f"⚠️  Blueprints directory not found: {BLUEPRINTS_DIR}")
            return blueprints
        
        for md_file in BLUEPRINTS_DIR.glob("*.md"):
            if md_file.name in ("README.md", "GUIDE-building-without-ai.md"):
                continue
            
            content = md_file.read_text(encoding="utf-8")
            blueprint = self._parse_blueprint(md_file.stem, content)
            if blueprint:
                blueprints[md_file.stem] = blueprint
        
        return blueprints
    
    def _parse_blueprint(self, name: str, content: str) -> Optional[Dict]:
        """Parse a blueprint markdown file into structured data."""
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split("\n"):
            if line.startswith("## "):
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                current_section = line[3:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = "\n".join(current_content)
        
        # Extract title from first H1
        title = name.replace("-", " ").title()
        for line in content.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break
        
        return {
            "name": name,
            "title": title,
            "sections": sections,
            "raw": content
        }
    
    def _get_blueprint_summaries(self) -> str:
        """Get a brief summary of each blueprint for the LLM."""
        summaries = []
        for name, bp in self.blueprints.items():
            core_purpose = bp["sections"].get("Core Purpose", "No description")[:200]
            summaries.append(f"- **{bp['title']}**: {core_purpose.strip()}")
        return "\n".join(summaries)
    
    def _get_dialogue_context(self, max_turns: int = 6) -> str:
        """Format recent dialogue history for prompts."""
        if not self.dialogue_history:
            return "(No prior dialogue)"
        
        context = []
        for entry in self.dialogue_history[-max_turns:]:
            role = "User" if entry["role"] == "user" else "Advisor"
            context.append(f"{role}: {entry['content']}")
        return "\n".join(context)
    
    def _add_to_history(self, role: str, content: str):
        """Add an entry to dialogue history."""
        self.dialogue_history.append({"role": role, "content": content})
    
    # ========================================================================
    # PUBLIC API - Main interaction methods
    # ========================================================================
    
    def start_discovery(self, initial_description: str = "") -> str:
        """
        Start the blueprint discovery process.
        
        Args:
            initial_description: Optional initial description of what they want to build
            
        Returns:
            The advisor's first question
        """
        self.current_mode = "discovery"
        self.dialogue_history = []
        self.selected_blueprint = None
        
        if initial_description:
            self._add_to_history("user", initial_description)
            self.user_context["initial_description"] = initial_description
        
        prompt = BLUEPRINT_DISCOVERY_PROMPT.format(
            blueprint_summaries=self._get_blueprint_summaries(),
            description=initial_description or "(No description yet)",
            dialogue_history=self._get_dialogue_context()
        )
        
        response = call_llm(prompt, ADVISOR_SYSTEM_PROMPT)
        self._add_to_history("advisor", response)
        
        return response
    
    def respond(self, user_input: str) -> str:
        """
        Continue the dialogue based on current mode.
        
        Args:
            user_input: The user's response
            
        Returns:
            The advisor's next question or recommendation
        """
        self._add_to_history("user", user_input)
        
        if self.current_mode == "discovery":
            return self._handle_discovery(user_input)
        elif self.current_mode == "features":
            return self._handle_features(user_input)
        elif self.current_mode == "mvp":
            return self._handle_mvp(user_input)
        elif self.current_mode == "stack":
            return self._handle_stack(user_input)
        else:
            return self._handle_discovery(user_input)
    
    def _handle_discovery(self, user_input: str) -> str:
        """Handle blueprint discovery phase."""
        # Check if we should recommend a blueprint
        if len(self.dialogue_history) >= 6:
            return self._make_recommendation()
        
        prompt = BLUEPRINT_DISCOVERY_PROMPT.format(
            blueprint_summaries=self._get_blueprint_summaries(),
            description=self.user_context.get("initial_description", user_input),
            dialogue_history=self._get_dialogue_context()
        )
        
        response = call_llm(prompt, ADVISOR_SYSTEM_PROMPT)
        self._add_to_history("advisor", response)
        return response
    
    def _make_recommendation(self) -> str:
        """Make a blueprint recommendation based on dialogue."""
        prompt = f"""Based on this dialogue, recommend the best blueprint:

AVAILABLE BLUEPRINTS:
{self._get_blueprint_summaries()}

DIALOGUE:
{self._get_dialogue_context(max_turns=10)}

Recommend ONE blueprint and explain why it fits.
Then ask if they'd like to customize features for it.
Keep it to 3-4 sentences."""
        
        response = call_llm(prompt, ADVISOR_SYSTEM_PROMPT)
        self._add_to_history("advisor", response)
        return response
    
    def _handle_features(self, user_input: str) -> str:
        """Handle feature customization phase."""
        bp = self.blueprints.get(self.selected_blueprint, {})
        features = bp.get("sections", {}).get("Feature Categories", "No features listed")
        
        prompt = FEATURE_DISCOVERY_PROMPT.format(
            blueprint_name=bp.get("title", self.selected_blueprint),
            features=features[:1000],  # Limit context size
            goal=self.user_context.get("initial_description", ""),
            dialogue_history=self._get_dialogue_context()
        )
        
        response = call_llm(prompt, ADVISOR_SYSTEM_PROMPT)
        self._add_to_history("advisor", response)
        return response
    
    def _handle_mvp(self, user_input: str) -> str:
        """Handle MVP scoping phase."""
        prompt = MVP_SCOPING_PROMPT.format(
            blueprint_name=self.selected_blueprint or "app",
            chosen_features=self.user_context.get("chosen_features", "Not specified"),
            dialogue_history=self._get_dialogue_context()
        )
        
        response = call_llm(prompt, ADVISOR_SYSTEM_PROMPT)
        self._add_to_history("advisor", response)
        return response
    
    def _handle_stack(self, user_input: str) -> str:
        """Handle technical stack selection phase."""
        bp = self.blueprints.get(self.selected_blueprint, {})
        stack = bp.get("sections", {}).get("Technical Stack (Recommended)", "No stack recommendations")
        
        prompt = STACK_ADVISOR_PROMPT.format(
            blueprint_name=bp.get("title", self.selected_blueprint),
            experience=self.user_context.get("experience", "Not specified"),
            constraints=self.user_context.get("constraints", "None mentioned"),
            stack_options=stack[:800],
            dialogue_history=self._get_dialogue_context()
        )
        
        response = call_llm(prompt, ADVISOR_SYSTEM_PROMPT)
        self._add_to_history("advisor", response)
        return response
    
    def select_blueprint(self, blueprint_name: str) -> str:
        """
        Select a specific blueprint and move to feature customization.
        
        Args:
            blueprint_name: Name of the blueprint (e.g., "learning-app")
            
        Returns:
            First question about feature customization
        """
        if blueprint_name not in self.blueprints:
            available = ", ".join(self.blueprints.keys())
            return f"Blueprint '{blueprint_name}' not found. Available: {available}"
        
        self.selected_blueprint = blueprint_name
        self.current_mode = "features"
        
        bp = self.blueprints[blueprint_name]
        return self._handle_features(f"I want to build a {bp['title']}")
    
    def set_mode(self, mode: str):
        """Change the current advisory mode."""
        valid_modes = ["discovery", "features", "mvp", "stack"]
        if mode in valid_modes:
            self.current_mode = mode
    
    def get_blueprint_content(self, name: str) -> Optional[str]:
        """Get the raw content of a blueprint."""
        bp = self.blueprints.get(name)
        return bp["raw"] if bp else None
    
    def list_blueprints(self) -> List[str]:
        """List all available blueprint names."""
        return list(self.blueprints.keys())


# ============================================================================
# CLI Interface
# ============================================================================

def run_cli():
    """Run the blueprint advisor as an interactive CLI."""
    print("\n" + "=" * 60)
    print("   🏛️  SOCRATIC BLUEPRINT ADVISOR")
    print("   Discover what you should build through dialogue")
    print("=" * 60 + "\n")
    
    advisor = BlueprintAdvisor()
    
    print("Describe what you want to build (or press Enter to explore):\n")
    initial = input("You: ").strip()
    
    response = advisor.start_discovery(initial)
    print(f"\n🎯 Advisor: {response}\n")
    
    print("Commands: /blueprints, /select <name>, /features, /mvp, /stack, /quit\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye! Good luck with your project.")
            break
        
        if not user_input:
            continue
        
        # Handle commands
        if user_input.startswith("/"):
            cmd = user_input.lower().split()
            
            if cmd[0] == "/quit":
                print("\nGoodbye! Good luck with your project.")
                break
            elif cmd[0] == "/blueprints":
                print("\nAvailable blueprints:")
                for name in advisor.list_blueprints():
                    print(f"  - {name}")
                print()
                continue
            elif cmd[0] == "/select" and len(cmd) > 1:
                response = advisor.select_blueprint(cmd[1])
            elif cmd[0] == "/features":
                advisor.set_mode("features")
                response = "Switching to feature customization. What features are most important to you?"
            elif cmd[0] == "/mvp":
                advisor.set_mode("mvp")
                response = "Let's scope your MVP. What's the ONE thing your app must do to be useful?"
            elif cmd[0] == "/stack":
                advisor.set_mode("stack")
                response = "Let's choose your tech stack. What programming languages are you comfortable with?"
            else:
                print("Unknown command. Try: /blueprints, /select <name>, /features, /mvp, /stack, /quit")
                continue
        else:
            response = advisor.respond(user_input)
        
        print(f"\n🎯 Advisor: {response}\n")


if __name__ == "__main__":
    run_cli()
