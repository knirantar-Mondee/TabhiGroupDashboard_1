import os
import sys
import glob
import pandas as pd
import openpyxl
from dotenv import load_dotenv
from openai import OpenAI

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import OUTPUT_DIR
from src.utils import logger

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

# Initialize OpenAI client
client = OpenAI(
    base_url="https://ollama.com/v1",
    api_key=os.getenv("OLLAMA_API_KEY", "dummy_key")
)
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-oss:20b-cloud")

SYSTEM_PROMPT = """You are an intelligence analyst. Read the following news article and categorize it into EXACTLY ONE of the following buckets:

Product Announcement
Tech Updates
Funding
Partnership and Acquisitions
Leadership Changes
Strategic Expansion or Changes
General Industry News

Return ONLY the category name, with no extra text."""

class IntelligenceEngine:
    """Identifies key competitive actions, threat level, and strategic implications based on LLM category."""
    def __init__(self):
        logger.debug("IntelligenceEngine initialized in categorizer job")

    def extract_insights(self, article_dict):
        category = article_dict.get("News_Category", "General Industry News")
        sentiment = article_dict.get("Sentiment", "Neutral")
        competitor = article_dict.get("Competitor", "Unknown")
        target_brand = article_dict.get("Target_Brand", "Miraee")
        
        is_own_brand = any(brand.lower() in competitor.lower() for brand in ["mondee", "miraee", "abhee", "abhi"])
        
        if is_own_brand:
            if sentiment == "Negative":
                threat = "High"
            else:
                threat = "Low"
        else:
            # Map new categories to threat assessment logic
            if category in ["Partnership and Acquisitions", "Product Announcement"] and sentiment == "Positive":
                threat = "High"
            elif category in ["Funding", "Strategic Expansion or Changes"] and sentiment == "Positive":
                threat = "Medium"
            elif sentiment == "Negative":
                threat = "Low"
            else:
                threat = "Low"
                
        if is_own_brand:
            action = f"Internal corporate {category.lower()} action by {competitor}"
        else:
            action = f"{competitor} executed {category.lower()} movement impacting {target_brand} market segment"
            
        if threat == "High":
            implication = f"High competitive activity. Monitor {competitor}'s {category.lower()} closely and evaluate defense strategies for {target_brand}."
        elif threat == "Medium":
            implication = f"Moderate competitive movement. Assess {target_brand}'s product positioning relative to {competitor}."
        else:
            if sentiment == "Negative" and not is_own_brand:
                implication = f"Potential opportunity. Competitor {competitor} is undergoing stress ({category.lower()}) which {target_brand} can capitalize on."
            else:
                implication = f"Standard market activity by {competitor}. No direct action required for {target_brand}."
            
        return {
            "threat_level": threat,
            "competitor_action": action,
            "strategic_implication": implication
        }


def categorize_article(title, body):
    text = f"Title: {title}\n\nBody: {body}"
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text[:3000]} # Limit text length to avoid token limits
            ],
            temperature=0.1
        )
        category = response.choices[0].message.content.strip()
        
        # Validate category
        valid_categories = [
            "Product Announcement", "Tech Updates", "Funding", 
            "Partnership and Acquisitions", "Leadership Changes", 
            "Strategic Expansion or Changes", "General Industry News"
        ]
        for valid in valid_categories:
            if valid.lower() in category.lower():
                return valid
        return "General Industry News"
        
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        return "General Industry News"

def run_categorization():
    logger.info("=========================================")
    logger.info("Starting LLM News Categorization Job")
    logger.info("=========================================")
    
    intel_engine = IntelligenceEngine()
    db_pattern = os.path.join(OUTPUT_DIR, "raw_news_database_*.xlsx")
    db_files = glob.glob(db_pattern)
    
    for db_file in db_files:
        logger.info(f"Processing database: {db_file}")
        
        try:
            wb = openpyxl.load_workbook(db_file)
            ws = wb["Raw_News"]
            
            # Find column indices
            header_list = list(next(ws.iter_rows(min_row=1, max_row=1, values_only=True)))
            
            # Self-heal historical data: if "Topic" exists instead of "News_Category", rename it
            if "Topic" in header_list and "News_Category" not in header_list:
                idx = header_list.index("Topic")
                ws.cell(row=1, column=idx + 1).value = "News_Category"
                header_list[idx] = "News_Category"
                wb.save(db_file)
                logger.info(f"Renamed legacy 'Topic' column to 'News_Category' in {db_file}")

            try:
                cat_idx = header_list.index("News_Category")
                title_idx = header_list.index("Title")
                body_idx = header_list.index("News_Body")
                comp_idx = header_list.index("Competitor")
                sent_idx = header_list.index("Sentiment")
                target_idx = header_list.index("Target_Brand")
                
                threat_idx = header_list.index("Threat_Level")
                action_idx = header_list.index("Competitor_Action")
                impl_idx = header_list.index("Strategic_Implication")
            except ValueError as e:
                logger.error(f"Missing required columns in {db_file}: {e}")
                continue
                
            updates_made = 0
            
            for row in ws.iter_rows(min_row=2):
                current_cat = row[cat_idx].value
                
                # Check if cell is empty or NaN-like
                if not current_cat or pd.isna(current_cat) or str(current_cat).strip() == "":
                    title = row[title_idx].value or ""
                    body = row[body_idx].value or ""
                    
                    if not title and not body:
                        continue
                        
                    logger.info(f"Categorizing article: {title[:50]}...")
                    category = categorize_article(title, body)
                    
                    # Update category cell
                    row[cat_idx].value = category
                    
                    # Run Intelligence Engine
                    art_dict = {
                        "News_Category": category,
                        "Competitor": row[comp_idx].value,
                        "Sentiment": row[sent_idx].value,
                        "Target_Brand": row[target_idx].value
                    }
                    insights = intel_engine.extract_insights(art_dict)
                    
                    # Update intelligence cells
                    row[threat_idx].value = insights["threat_level"]
                    row[action_idx].value = insights["competitor_action"]
                    row[impl_idx].value = insights["strategic_implication"]
                    
                    updates_made += 1
                    
            if updates_made > 0:
                wb.save(db_file)
                logger.info(f"Saved {updates_made} updates to {db_file}")
                
                # Copy the updated file to the dashboard directory
                import shutil
                dashboard_dir = os.path.join(os.path.dirname(os.path.dirname(OUTPUT_DIR)), "News_Dashboard", "data")
                if os.path.exists(dashboard_dir):
                    filename = os.path.basename(db_file)
                    dashboard_file_path = os.path.join(dashboard_dir, filename)
                    shutil.copy2(db_file, dashboard_file_path)
                    logger.info(f"Synced {filename} to dashboard data folder.")
            else:
                logger.info("No uncategorized rows found.")
                
            wb.close()
            
        except Exception as e:
            logger.error(f"Error processing {db_file}: {e}")
            
    logger.info("=========================================")
    logger.info("Categorization Job completed.")
    logger.info("=========================================")

if __name__ == "__main__":
    run_categorization()
