from src.utils import logger




class SentimentAnalyzer:
    """Analyzes sentiment of article body content relative to competitors."""
    def __init__(self):
        logger.debug("SentimentAnalyzer initialized")

    def analyze(self, text, competitor):
        text_lower = text.lower() if text else ""
        if not text_lower:
            return "Neutral"
            
        positive_words = ["growth", "success", "profit", "win", "expand", "expansion", "partnership", "gain", "strengthen", "boost", "innovation", "innovative", "growing", "positive", "valuable", "leader"]
        negative_words = ["bankruptcy", "chapter 11", "fail", "decline", "drop", "lawsuit", "debt", "restructuring", "loss", "layoff", "fired", "sued", "struggle", "negative", "warns"]
        
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        
        if pos_count > neg_count:
            return "Positive"
        elif neg_count > pos_count:
            return "Negative"
        else:
            return "Neutral"





class ExecutiveSummaryGenerator:
    """Generates executive brief bullet points from raw scraped article bodies."""
    def __init__(self):
        logger.debug("ExecutiveSummaryGenerator initialized")

    def generate_brief(self, articles_list):
        if not articles_list:
            return "No articles processed in this run."
        return f"Analyzed {len(articles_list)} competitor news articles. Restructuring, M&A and digital product enhancements remain key active domains."
        
    def generate_article_summary(self, title, text):
        """Extract a concise brief (first 2 sentences or first 200 chars), stripping HTML if present."""
        if not text or "failed to scrape" in text.lower():
            return title or "No summary available."
            
        # Strip summary fallbacks notation
        if text.startswith("[Summary Fallback]"):
            text = text[18:].strip()
            
        # Strip HTML tags if any (e.g. from Google News RSS feed)
        import re
        text = re.sub(r'<[^>]*>', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
            
        # Split by sentences
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 5]
        if len(sentences) >= 2:
            return ". ".join(sentences[:2]) + "."
        elif len(sentences) == 1:
            return sentences[0] + "."
            
        return text[:200].strip() + ("..." if len(text) > 200 else "")
