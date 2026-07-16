import os
import sys
import pandas as pd
from apify_client import ApifyClient
from dotenv import load_dotenv

# Add src parent folder to python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import BASE_DIR
from src.categorizer_job import client as openai_client, MODEL_NAME as llm_model
from src.utils import logger

# Import platform scrapers
from src.social_media.x_scraper import scrape_x
from src.social_media.instagram_scraper import scrape_instagram
from src.social_media.linkedin_scraper import scrape_linkedin
from src.social_media.youtube_scraper import scrape_youtube

# Import LLM insights engine
from src.social_media.insights_engine import analyze_post_with_llm, analyze_video_with_llm

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

# Config Paths
COMPETITORS_EXCEL_PATH = os.path.join(BASE_DIR, "input", "competitors.xlsx")
RUBRIC_EXCEL_PATH = os.path.join(BASE_DIR, "config", "scoring_rubric.xlsx")
OUTPUT_EXCEL_PATH = os.path.join(os.path.dirname(BASE_DIR), "News_Dashboard", "data", "social_media_posts.xlsx")

APIFY_API_TOKEN = os.getenv("APIFY_API_KEY") or "apify_api_VJxWA3U9RTuHIkQWlAcnK9sxWyXvmo1TubK1"
# Target handles map
COMPETITOR_HANDLES = {
    "Navan": {
        "x": "navan", "instagram": "getnavan", "linkedin": "navan", "youtube": "GetNavan"
    },
    "TravelPerk": {
        "x": "perkdotcom", "instagram": "perkdotcom", "linkedin": "travelperk", "youtube": "perk.global"
    },
    "SAP Concur": {
        "x": "SAPConcur", "instagram": "sapconcur", "linkedin": "sap-concur", "youtube": "SAPConcur"
    },
    "Ramp": {
        "x": "tryramp", "instagram": "tryramp", "linkedin": "ramp-card", "youtube": "Ramp"
    },
    "Brex": {
        "x": "brexhq", "instagram": "brex", "linkedin": "brex", "youtube": "BrexHQ"
    },
    "AirBnb": {
        "x": "Airbnb", "instagram": "airbnb", "linkedin": "airbnb", "youtube": "Airbnb"
    },
    "TripGenie": {
        "x": "Tripcom", "instagram": "trip", "linkedin": "trip.com", "youtube": "Trip.com"
    },
    "Expedia": {
        "x": "Expedia", "instagram": "expedia", "linkedin": "expedia", "youtube": "Expedia"
    },
    "Booking.com": {
        "x": "bookingcom", "instagram": "bookingcom", "linkedin": "booking.com", "youtube": "bookingcom"
    },
    "Centrav": {
        "x": "Centrav", "instagram": "centrav", "linkedin": "centrav-inc-", "youtube": "Centrav"
    },
    "Picasso Travel": {
        "x": "PicassoTravel", "instagram": "picassotravel", "linkedin": "picasso-travel", "youtube": None
    },
    "Sky Bird Travel": {
        "x": "SkyBirdTravel", "instagram": "skybirdtravel", "linkedin": "sky-bird-travel-&-tours", "youtube": None
    },
    "GTT Global": {
        "x": "GTTGlobal", "instagram": None, "linkedin": "gttglobal", "youtube": None
    },
    "Downtown Travel": {
        "x": "DowntownTravel", "instagram": None, "linkedin": "downtown-travel", "youtube": None
    },
    "Expedia TAAP": {
        "x": "ExpediaGroup", "instagram": None, "linkedin": "expediataap", "youtube": None
    },
    "Booking.com for Travel Agents": {
        "x": "bookingcom", "instagram": None, "linkedin": "booking-com-partner-services", "youtube": None
    },
    "Priceline Partner Network": {
        "x": "priceline", "instagram": None, "linkedin": "priceline-partner-network", "youtube": None
    }
}

def run_social_pipeline():
    logger.info("=========================================")
    logger.info("Starting Competitor Social Media Pipeline")
    logger.info("=========================================")
    
    # 1. Load Dynamic Categories
    logger.info(f"Loading dynamic categories from '{RUBRIC_EXCEL_PATH}'...")
    try:
        df_rubric = pd.read_excel(RUBRIC_EXCEL_PATH, sheet_name="Category_Weights")
        categories_list = df_rubric["Category"].dropna().str.strip().tolist()
        logger.info(f"Loaded {len(categories_list)} categories: {categories_list}")
    except Exception as e:
        logger.error(f"Error reading scoring_rubric.xlsx: {str(e)}")
        return

    # 2. Load Competitors List
    logger.info(f"Loading competitors configuration from '{COMPETITORS_EXCEL_PATH}'...")
    try:
        df_competitors = pd.read_excel(COMPETITORS_EXCEL_PATH, sheet_name="Competitors")
        logger.info(f"Loaded {len(df_competitors)} competitors.")
    except Exception as e:
        logger.error(f"Error reading competitors.xlsx: {str(e)}")
        return

    apify_client = ApifyClient(APIFY_API_TOKEN)
    logger.info(f"🤖 Using active LLM connection with model {llm_model}...")

    limit_per_platform = 5
    combined_posts = []

    # 3. Iterate and Scrape
    for idx, row in df_competitors.iterrows():
        competitor_name = row["Competitor"]
        base_company = row["Base"]
        
        logger.info(f"Processing Competitor [{competitor_name}] competing with [{base_company}]")
        
        handles = COMPETITOR_HANDLES.get(competitor_name)
        if not handles:
            logger.warn(f"Handles not configured for '{competitor_name}'. Skipping.")
            continue
            
        raw_posts = []
        
        # Scrape X/Twitter
        if handles.get("x"):
            x_posts = scrape_x(apify_client, username=handles["x"], limit=limit_per_platform)
            for p in x_posts:
                p["Platform"] = "X (Twitter)"
                raw_posts.append(p)
                
        # Scrape Instagram
        if handles.get("instagram"):
            insta_posts = scrape_instagram(apify_client, username=handles["instagram"], limit=limit_per_platform)
            for p in insta_posts:
                p["Platform"] = "Instagram"
                raw_posts.append(p)
                
        # Scrape LinkedIn
        if handles.get("linkedin"):
            linkedin_url = f"https://www.linkedin.com/company/{handles['linkedin']}"
            li_posts = scrape_linkedin(apify_client, company_url=linkedin_url, limit=limit_per_platform)
            for p in li_posts:
                p["Platform"] = "LinkedIn"
                raw_posts.append(p)
                
        # Scrape YouTube
        if handles.get("youtube"):
            yt_videos = scrape_youtube(apify_client, channel_handle=handles["youtube"], limit=limit_per_platform)
            for p in yt_videos:
                p["Platform"] = "YouTube"
                raw_posts.append(p)
                
        # LLM Insights Engine
        logger.info(f"Generating LLM Insights for {competitor_name} ({len(raw_posts)} total entries)...")
        for post in raw_posts:
            platform = post["Platform"]
            post_text = post.get("Post Text") or ""
            image_url = post.get("Image URL") or ""
            image_text = post.get("Image Text") or ""
            video_url = post.get("Video URL") or ""
            
            if platform == "YouTube":
                video_title = post_text.split("\n\n")[0]
                ai_insights = analyze_video_with_llm(
                    openai_client=openai_client,
                    model_name=llm_model,
                    video_url=video_url,
                    video_title=video_title,
                    categories_list=categories_list
                )
                video_transcript = ai_insights.get("transcript", "")
            else:
                video_transcript = post.get("Video Transcript") or ""
                ai_insights = analyze_post_with_llm(
                    openai_client=openai_client,
                    model_name=llm_model,
                    platform=platform,
                    competitor=competitor_name,
                    post_text=post_text,
                    image_text=image_text,
                    video_transcript=video_transcript,
                    categories_list=categories_list
                )

            # Consolidate standard structure
            combined_posts.append({
                "Base_Company": base_company,
                "Competitor": competitor_name,
                "Platform": platform,
                "Author/Handle": post.get("Author/Handle") or "",
                "Date Created": post.get("Date Created") or post.get("timestamp") or "",
                "Post Text": post_text,
                "Image URL": image_url,
                "Image Text": image_text,
                "Video URL": video_url,
                "Video Transcript": video_transcript,
                "Post URL": post.get("Post URL") or "",
                "Sentiment": ai_insights.get("sentiment", "Neutral"),
                "Category": ai_insights.get("category", "General Industry News"),
                "Alert Level": ai_insights.get("alert_level", "Low"),
                "AI Summary": ai_insights.get("summary", "Failed to analyze post.")
            })

    # 4. Save results to Excel sheet
    logger.info(f"Writing results to '{OUTPUT_EXCEL_PATH}'...")
    write_to_excel_safe(OUTPUT_EXCEL_PATH, combined_posts)

def write_to_excel_safe(output_file, combined_data):
    if not combined_data:
        logger.warn("⚠️ Warning: Combined social media posts dataset is EMPTY. Bypassing write to protect existing data!")
        return
    try:
        df = pd.DataFrame(combined_data)
        desired_columns = [
            "Base_Company", "Competitor", "Platform", "Author/Handle", "Date Created",
            "Post Text", "Image URL", "Image Text", "Video URL", "Video Transcript",
            "Post URL", "Sentiment", "Category", "Alert Level", "AI Summary"
        ]
        df = df.reindex(columns=desired_columns)
        
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Social_Media_Insights", index=False)
            logger.info("Successfully wrote all rows to sheet: Social_Media_Insights")
        logger.info("Competitor Social Media Pipeline completed successfully.")
    except PermissionError:
        fallback_file = output_file.replace(".xlsx", "_new.xlsx")
        logger.warn(f"Permission denied writing to '{output_file}'. Writing to fallback: '{fallback_file}'")
        write_to_excel_safe(fallback_file, combined_data)
    except Exception as e:
        logger.error(f"Error writing to Excel file: {str(e)}")

if __name__ == "__main__":
    run_social_pipeline()
