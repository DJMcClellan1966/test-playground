"""
Standard Interrogation Prompts

These prompts are the "artificial questioner" - they systematically extract
knowledge from authoritative texts in a way that makes the content accessible
to novices.

The key insight: A novice doesn't know what questions to ask. These prompts
ask the questions a good teacher would answer before diving into material.
"""

# The complete interrogation that extracts a knowledge layer from a section
FULL_EXTRACTION_PROMPT = """You are extracting knowledge from an authoritative text to help novices learn.

Analyze the following section and extract structured knowledge. Be precise and cite the text directly when possible.

TEXT:
{text}

---

Extract the following (use "Not specified in text" if information isn't present):

## Overview
[One paragraph: What is this section about? What will the reader learn?]

## Prerequisites
[What must the reader already understand before this section makes sense?]
- List each prerequisite concept

## Key Terms
[Define each important term introduced in this section]
- **Term**: Definition (cite text if possible)

## Main Claims
[What are the central ideas, theorems, or assertions?]
1. Claim (with brief justification from text)

## Key Steps/Process
[If the section describes a procedure or algorithm, list the steps]
1. Step (what it does and why)

## Concrete Examples
[What examples illustrate the concepts? Explain each]
- Example: What it demonstrates

## Common Pitfalls
[What mistakes might a reader make? What's easy to misunderstand?]
- Pitfall: Why it's a problem

## Connections
[What other concepts does this relate to?]
- Connection: How it relates

## One-Sentence Summary
[Capture the essence in one sentence a novice could understand]
"""

# Targeted prompts for specific follow-up questions
EXPLAIN_TERM_PROMPT = """Based on this authoritative text:

{text}

---

Explain the term "{term}" to someone who has never encountered it.

1. Start with a simple, one-sentence definition
2. Explain why this term matters
3. Give a concrete example
4. Clarify what this term is NOT (common misconceptions)
5. Quote the text's definition if available

Be precise. Only state what's in the text or can be directly inferred.
"""

EXPLAIN_CONCEPT_PROMPT = """Based on this authoritative text:

{text}

---

The user wants to understand: "{concept}"

Explain this thoroughly:
1. What is it? (simple definition)
2. Why does it matter? (significance)
3. How does it work? (mechanism, step by step if applicable)
4. What's an example? (concrete illustration)
5. What connects to this? (related ideas in the text)

Use only information from the text. Quote specific passages when helpful.
"""

TRACE_EXAMPLE_PROMPT = """Based on this authoritative text:

{text}

---

The user wants to see an example of: "{topic}"

1. Find the most relevant example in the text
2. Walk through it step by step
3. Explain what each step demonstrates
4. Connect back to the general principle

If the text provides a worked example, trace through it. If not, create one that's consistent with the text's definitions.
"""

CHALLENGE_ANSWER_PROMPT = """The user is learning from this authoritative text:

{text}

---

You previously provided this answer:
{previous_answer}

The user challenges: "{challenge}"

Re-examine the source text and:
1. Is the challenge valid? Does the text support a different interpretation?
2. Quote the specific passages that support the correct answer
3. If you were wrong, correct it
4. If you were right, explain why using text evidence

Be intellectually honest. The text is the source of truth.
"""

PREREQUISITE_CHECK_PROMPT = """Based on this authoritative text:

{text}

---

Before learning this material, what should someone already understand?

1. List each prerequisite concept
2. For each, explain:
   - What it is (brief)
   - Why it's needed for this material
   - How to tell if you understand it well enough
3. Order from most basic to most advanced

Be specific. Don't say "basic math" - say "integer division with remainders".
"""

SUMMARY_LEVELS_PROMPT = """Based on this authoritative text:

{text}

---

Create summaries at three levels:

## For a 10-year-old (ELI10)
[Explain the core idea in simple terms, using analogies if helpful]

## For a student (Standard)
[A paragraph covering the main concepts and why they matter]

## For a practitioner (Technical)
[Dense summary assuming familiarity with the field, focus on precise details]
"""

# System prompt that establishes how the AI should behave
SYSTEM_PROMPT = """You are a Socratic learning assistant. Your role is to help users understand authoritative texts.

Rules:
1. ONLY answer from the provided text. If information isn't in the text, say so.
2. ALWAYS cite your sources by quoting relevant passages.
3. When uncertain, express uncertainty. Don't make things up.
4. Encourage deeper exploration - suggest follow-up questions the user might ask.
5. If the user challenges your answer, re-examine the text honestly.

Your goal is to help the user reach understanding, not to show off knowledge.
"""


def get_extraction_prompt(text: str) -> str:
    """Get the prompt to extract a full knowledge layer from text."""
    return FULL_EXTRACTION_PROMPT.format(text=text)


def get_explain_term_prompt(text: str, term: str) -> str:
    """Get the prompt to explain a specific term."""
    return EXPLAIN_TERM_PROMPT.format(text=text, term=term)


def get_explain_concept_prompt(text: str, concept: str) -> str:
    """Get the prompt to explain a concept in depth."""
    return EXPLAIN_CONCEPT_PROMPT.format(text=text, concept=concept)


def get_trace_example_prompt(text: str, topic: str) -> str:
    """Get the prompt to walk through an example."""
    return TRACE_EXAMPLE_PROMPT.format(text=text, topic=topic)


def get_challenge_prompt(text: str, previous_answer: str, challenge: str) -> str:
    """Get the prompt when user challenges a previous answer."""
    return CHALLENGE_ANSWER_PROMPT.format(
        text=text, 
        previous_answer=previous_answer, 
        challenge=challenge
    )


def get_prerequisite_prompt(text: str) -> str:
    """Get the prompt to identify prerequisites."""
    return PREREQUISITE_CHECK_PROMPT.format(text=text)


def get_summary_prompt(text: str) -> str:
    """Get the prompt for multi-level summaries."""
    return SUMMARY_LEVELS_PROMPT.format(text=text)
