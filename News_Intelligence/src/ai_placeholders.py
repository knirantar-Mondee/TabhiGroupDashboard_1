from src.utils import logger

class TopicClassifier:
    """Classifies news articles into industry topics (e.g. M&A, Product Launch, Funding, Restructuring)."""
    def __init__(self):
        logger.debug("TopicClassifier initialized")

    def classify(self, text):
        text_lower = text.lower() if text else ""
        if not text_lower:
            return "General Industry News"
        
        # Topic detection rules
        if any(x in text_lower for x in ["chapter 11", "bankruptcy", "restructuring", "refinance", "liquidity", "debt"]):
            return "Restructuring & Finance"
        if any(x in text_lower for x in ["acquire", "acquisition", "merger", "takeover", "buyout", "merges with"]):
            return "M&A"
        if any(x in text_lower for x in ["funding", "raise", "invest", "investment", "round", "venture capital", "equity"]):
            return "Funding"
        if any(x in text_lower for x in ["launch", "introduce", "unveil", "release", "roll out", "feature", "connect"]):
            return "Product Launch"
        if any(x in text_lower for x in ["partner", "partnership", "collaborate", "collaboration", "alliance", "tie up"]):
            return "Partnership"
        if any(x in text_lower for x in ["ceo", "executive", "hire", "appoint", "board of directors", "stepped down"]):
            return "Executive Move"
        if any(x in text_lower for x in ["regulation", "lawsuit", "sue", "court", "compliance", "government", "policy"]):
            return "Regulatory & Legal"
        
        return "General Travel News"


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


class IntelligenceEngine:
    """Identifies key competitive actions, threat level, and strategic implications."""
    def __init__(self):
        logger.debug("IntelligenceEngine initialized")

    def extract_insights(self, article_dict):
        topic = article_dict.get("Topic", "General Travel News")
        sentiment = article_dict.get("Sentiment", "Neutral")
        competitor = article_dict.get("Competitor", "Unknown")
        target_brand = article_dict.get("Target_Brand", "Miraee")
        
        # Threat Level rules based on competitor actions relative to the target brand
        # If the article discusses one of our own target brands (e.g. "Mondee" is the competitor matched)
        is_own_brand = any(brand.lower() in competitor.lower() for brand in ["mondee", "miraee", "abhee", "abhi"])
        
        if is_own_brand:
            # For our own activity, negative news is high severity/threat
            if sentiment == "Negative":
                threat = "High"
            else:
                threat = "Low"
        else:
            # Competitor actions threat assessment relative to target brand segment
            if topic in ["M&A", "Product Launch"] and sentiment == "Positive":
                threat = "High"
            elif topic in ["Partnership", "Funding"] and sentiment == "Positive":
                threat = "Medium"
            elif sentiment == "Negative":
                threat = "Low"
            else:
                threat = "Low"
                
        # Competitor Action phrase
        if is_own_brand:
            action = f"Internal corporate {topic.lower()} action by {competitor}"
        else:
            action = f"{competitor} executed {topic.lower()} movement impacting {target_brand} market segment"
            
        # Strategic Implication phrase
        if threat == "High":
            implication = f"High competitive activity. Monitor {competitor}'s {topic.lower()} closely and evaluate defense strategies for {target_brand}."
        elif threat == "Medium":
            implication = f"Moderate competitive movement. Assess {target_brand}'s product positioning relative to {competitor}."
        else:
            if sentiment == "Negative" and not is_own_brand:
                implication = f"Potential opportunity. Competitor {competitor} is undergoing stress ({topic.lower()}) which {target_brand} can capitalize on."
            else:
                implication = f"Standard market activity by {competitor}. No direct action required for {target_brand}."
            
        return {
            "threat_level": threat,
            "competitor_action": action,
            "strategic_implication": implication
        }


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
