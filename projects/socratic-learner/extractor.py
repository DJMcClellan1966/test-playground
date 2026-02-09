"""
Knowledge Extractor

Runs the Standard Interrogation on source texts to extract knowledge layers.
"""

import os
import re
import json
import time
from pathlib import Path
from typing import List, Dict, Optional

import config
from llm_client import call_llm
from prompts.standard_interrogation import (
    get_extraction_prompt,
    SYSTEM_PROMPT
)


def parse_markdown_sections(content: str) -> List[Dict]:
    """
    Split markdown content into sections based on ## headers.
    
    Returns list of {title, level, content} dicts.
    """
    sections = []
    current_section = {"title": "Introduction", "level": 0, "content": ""}
    
    lines = content.split('\n')
    
    for line in lines:
        # Check for headers
        header_match = re.match(r'^(#{1,3})\s+(.+)$', line)
        
        if header_match:
            # Save previous section if it has content
            if current_section["content"].strip():
                sections.append(current_section)
            
            level = len(header_match.group(1))
            title = header_match.group(2)
            current_section = {
                "title": title,
                "level": level,
                "content": ""
            }
        else:
            current_section["content"] += line + "\n"
    
    # Don't forget the last section
    if current_section["content"].strip():
        sections.append(current_section)
    
    return sections


def _cache_path_for_source(source_path: str) -> Path:
    source_name = Path(source_path).stem
    return Path(config.EXTRACTION_CACHE_DIR) / f"{source_name}_sections.json"


def _load_cached_sections(source_path: str) -> Optional[List[Dict]]:
    cache_path = _cache_path_for_source(source_path)
    if not cache_path.exists():
        return None

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception:
        return None

    try:
        stat = os.stat(source_path)
    except OSError:
        return None

    if payload.get("mtime") != stat.st_mtime or payload.get("size") != stat.st_size:
        return None

    return payload.get("sections")


def _save_cached_sections(source_path: str, sections: List[Dict]) -> None:
    cache_path = _cache_path_for_source(source_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        stat = os.stat(source_path)
    except OSError:
        return

    payload = {
        "source": source_path,
        "mtime": stat.st_mtime,
        "size": stat.st_size,
        "sections": sections,
    }

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _looks_like_error(text: str) -> bool:
    if not text:
        return True
    lowered = text.strip().lower()
    return lowered.startswith("error") or "error connecting to ollama" in lowered


def _extract_with_retry(prompt: str, system_prompt: str, model_override: Optional[str]) -> str:
    last_response = ""
    for attempt in range(config.EXTRACTION_RETRIES + 1):
        response = call_llm(prompt, system_prompt, model_override=model_override)
        last_response = response
        if not _looks_like_error(response):
            return response
        if attempt < config.EXTRACTION_RETRIES:
            time.sleep(config.EXTRACTION_RETRY_DELAY_SEC)
    return last_response


def extract_knowledge(source_path: str, output_path: Optional[str] = None) -> Dict:
    """
    Extract knowledge layer from a source document.
    
    Args:
        source_path: Path to the markdown source file
        
    Returns:
        Dictionary containing the extracted knowledge
    """
    print(f"📖 Loading source: {source_path}")
    
    with open(source_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse into sections (cached)
    sections = _load_cached_sections(source_path)
    if sections is None:
        sections = parse_markdown_sections(content)
        _save_cached_sections(source_path, sections)
    print(f"📑 Found {len(sections)} sections")
    
    knowledge = {
        "source_file": source_path,
        "sections": [],
        "full_text": content
    }

    existing_titles = set()
    if output_path and os.path.exists(output_path):
        try:
            existing = load_knowledge(output_path)
            knowledge["sections"] = existing.get("sections", [])
            knowledge["full_text"] = existing.get("full_text", content)
            for section in knowledge["sections"]:
                title = section.get("title")
                if title:
                    existing_titles.add(title)
            print(f"🔁 Resuming from existing output ({len(existing_titles)} sections)")
        except Exception:
            pass
    
    # Extract knowledge from each major section (level 1 or 2 headers with content)
    major_sections = [s for s in sections if s["level"] <= 2 and len(s["content"].strip()) > 100]
    
    # If we found very few, also include level 3
    if len(major_sections) < 3:
        major_sections = [s for s in sections if len(s["content"].strip()) > 100]
    
    for i, section in enumerate(major_sections):
        print(f"🔍 Extracting from: {section['title']} ({i+1}/{len(major_sections)})")

        if section["title"] in existing_titles:
            print("   ↪ Skipping (already extracted)")
            continue
        
        # Build context: include section content and a bit of surrounding context
        section_text = f"# {section['title']}\n\n{section['content']}"
        
        # Run extraction
        prompt = get_extraction_prompt(section_text)
        extraction = _extract_with_retry(prompt, SYSTEM_PROMPT, config.OLLAMA_EXTRACT_MODEL)
        
        knowledge["sections"].append({
            "title": section["title"],
            "level": section["level"],
            "original_content": section["content"],
            "extracted_knowledge": extraction
        })

        if output_path:
            save_knowledge(knowledge, output_path)
    
    return knowledge


def save_knowledge(knowledge: Dict, output_path: str):
    """Save extracted knowledge to a JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(knowledge, f, indent=2)
    print(f"💾 Saved knowledge to: {output_path}")


def load_knowledge(path: str) -> Dict:
    """Load previously extracted knowledge."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """Run extraction on a source file."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python extractor.py <source_file>")
        print("Example: python extractor.py sources/algorithms_intro.md")
        sys.exit(1)
    
    source_path = sys.argv[1]
    
    if not os.path.exists(source_path):
        print(f"Error: Source file not found: {source_path}")
        sys.exit(1)
    
    # Save to knowledge directory
    os.makedirs(config.KNOWLEDGE_DIR, exist_ok=True)
    source_name = Path(source_path).stem
    output_path = os.path.join(config.KNOWLEDGE_DIR, f"{source_name}_knowledge.json")

    # Extract knowledge (resume + incremental saves)
    knowledge = extract_knowledge(source_path, output_path)
    
    print("\n✅ Extraction complete!")
    print(f"   Sections processed: {len(knowledge['sections'])}")
    print(f"   Output: {output_path}")
    print(f"\nNext: Run 'python explorer.py' to explore the knowledge")


if __name__ == "__main__":
    main()
