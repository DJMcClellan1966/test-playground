"""
corpus_search.py

Module for searching local and online code/doc corpora for relevant information to fill templates or optimize models.
"""

import os
import re
from typing import List, Dict, Optional, Any

class CorpusSearch:
    def __init__(self, local_dirs: Optional[List[str]] = None):
        self.local_dirs = local_dirs or []

    def search_local(self, query: str, file_patterns: Optional[List[str]] = None, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search local directories for files matching the query.
        Returns a list of dicts: {path, snippet, score}
        """
        results = []
        patterns = file_patterns or [".py", ".md", ".txt"]
        for root_dir in self.local_dirs:
            for dirpath, _, filenames in os.walk(root_dir):
                for fname in filenames:
                    if any(fname.endswith(p) for p in patterns):
                        fpath = os.path.join(dirpath, fname)
                        try:
                            with open(fpath, encoding="utf-8", errors="ignore") as f:
                                text = f.read()
                            for m in re.finditer(re.escape(query), text, re.IGNORECASE):
                                snippet = text[max(0, m.start()-40):m.end()+40]
                                results.append({
                                    "path": fpath,
                                    "snippet": snippet,
                                    "score": 1.0  # Simple match, can be improved
                                })
                                if len(results) >= max_results:
                                    return results
                        except Exception:
                            continue
        return results

    def search_online(self, query: str, sources: Optional[List[str]] = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Placeholder for online search (e.g., Stack Overflow, GitHub, Wikipedia).
        Returns a list of dicts: {source, snippet, url, score}
        """
        # Not implemented: would require API keys and network access
        return []

# Example usage:
# cs = CorpusSearch(["../patterns", "../docs"])
# results = cs.search_local("sqlite crud")
# print(results)
