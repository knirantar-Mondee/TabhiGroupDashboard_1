import re
from src.utils import logger, clean_text

class KeywordMatcher:
    def __init__(self, queries_dict):
        """
        queries_dict format: {
            "CompetitorName": [("QueryString", "QueryType"), ...]
        }
        """
        self.queries_dict = queries_dict
        self.compiled_patterns = self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        compiled = {}
        for competitor, query_list in self.queries_dict.items():
            compiled[competitor] = []
            for query, q_type in query_list:
                cleaned_query = query.strip()
                if not cleaned_query:
                    continue
                # Match query as a whole word boundary to prevent substring false matches (e.g. "Ramp" matching "Trampoline")
                # We use IGNORECASE flag
                pattern_str = r'\b' + re.escape(cleaned_query.lower()) + r'\b'
                try:
                    pattern = re.compile(pattern_str, re.IGNORECASE)
                    compiled[competitor].append({
                        "original_query": cleaned_query,
                        "type": q_type,
                        "pattern": pattern
                    })
                except re.error as e:
                    logger.error(f"Error compiling pattern for query '{cleaned_query}': {e}")
        return compiled

    def match_article(self, title, summary):
        """
        Check if article matches any competitor search queries.
        Returns a tuple of (matched_competitors_str, matched_queries_str) or (None, None).
        """
        text_to_search = clean_text(title) + " " + clean_text(summary)
        
        matched_comps = []
        matched_details = []
        
        for competitor, queries in self.compiled_patterns.items():
            is_comp_matched = False
            comp_matched_queries = []
            
            for q_info in queries:
                pattern = q_info["pattern"]
                if pattern.search(text_to_search):
                    is_comp_matched = True
                    orig_query = q_info["original_query"]
                    q_type = q_info["type"]
                    comp_matched_queries.append(f"{orig_query} ({q_type})")
            
            if is_comp_matched:
                matched_comps.append(competitor)
                matched_details.append("; ".join(comp_matched_queries))
                
        if matched_comps:
            return ", ".join(matched_comps), " | ".join(matched_details)
            
        return None, None
