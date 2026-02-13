"""
template_filler.py

Module for automatically filling templates using information from corpus search and user input.
"""

from typing import Dict, Any, Optional, List
from corpus_search import CorpusSearch

class TemplateFiller:
    def __init__(self, corpus_dirs: Optional[List[str]] = None):
        self.corpus_search = CorpusSearch(corpus_dirs)

    def fill_template(self, template: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """
        Fills a template dict using user input and relevant corpus snippets.
        Returns a filled template dict.
        """
        filled = template.copy()
        # 1. Use user input directly for obvious fields
        for k in filled:
            if isinstance(filled[k], str) and not filled[k]:
                if k in user_input:
                    filled[k] = user_input
        # 2. Search corpus for missing fields
        for k, v in filled.items():
            if not v:
                results = self.corpus_search.search_local(k)
                if results:
                    filled[k] = results[0]["snippet"]
        return filled

# Example usage:
# tf = TemplateFiller(["../patterns", "../docs"])
# template = {"name": "", "description": "", "db_schema": ""}
# filled = tf.fill_template(template, "recipe app with ingredients")
# print(filled)
