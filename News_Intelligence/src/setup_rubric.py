import pandas as pd
import os

def create_rubric():
    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_dir = os.path.join(base_dir, "config")
    
    # Ensure config dir exists
    os.makedirs(config_dir, exist_ok=True)
    
    excel_path = os.path.join(config_dir, "scoring_rubric.xlsx")
    
    # 1. Category Weights & UI Mapping
    category_data = {
        "Category": [
            "Partnership and Acquisitions",
            "Funding",
            "Leadership Changes",
            "Product Announcement",
            "Strategic Expansion or Changes",
            "Tech Updates",
            "General Industry News"
        ],
        "Points": [40, 35, 30, 25, 20, 10, 5],
        "UI_Tab_Mapping": [
            "Growth", 
            "Growth", 
            "Growth", 
            "Product", 
            "Overview", 
            "Product", 
            "Overview"
        ]
    }
    df_cat = pd.DataFrame(category_data)
    
    # 2. Competitor Tiers
    comp_data = {
        "Competitor_Name": [
            "Navan", "TripActions", "TravelPerk", # Tier 1
            "Egencia", "Concur", "Spotnana",      # Tier 2
            "Brex", "Ramp"                        # Tier 3
        ],
        "Points": [30, 30, 30, 15, 15, 15, 5, 5]
    }
    df_comp = pd.DataFrame(comp_data)
    
    # 3. Sentiment Multipliers
    sentiment_data = {
        "Scenario": [
            "Negative_Opportunity", # Competitor is doing bad
            "Positive_Threat",      # Competitor is doing good
            "Neutral_Default"
        ],
        "Points": [15, 10, 0]
    }
    df_sent = pd.DataFrame(sentiment_data)
    
    # 4. Keyword Boosts
    keyword_data = {
        "Keyword": [
            "acquires", "layoffs", "bankrupt", "ipo", "series", "millions"
        ],
        "Points": [15, 15, 15, 10, 10, 5]
    }
    df_key = pd.DataFrame(keyword_data)
    
    # 5. Time Decay
    decay_data = {
        "Age_In_Days": [0, 1, 3, 7, 14, 30, 365],
        "Multiplier": [1.5, 1.2, 1.0, 0.8, 0.5, 0.2, 0.0]
    }
    df_decay = pd.DataFrame(decay_data)
    
    # Write to Excel
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df_cat.to_excel(writer, sheet_name="Category_Weights", index=False)
        df_comp.to_excel(writer, sheet_name="Competitor_Tiers", index=False)
        df_sent.to_excel(writer, sheet_name="Sentiment_Multipliers", index=False)
        df_key.to_excel(writer, sheet_name="Keyword_Boosts", index=False)
        df_decay.to_excel(writer, sheet_name="Time_Decay", index=False)
        
    print(f"Successfully generated {excel_path}")

if __name__ == "__main__":
    create_rubric()
