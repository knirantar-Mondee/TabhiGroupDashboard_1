import os
import pandas as pd
from datetime import datetime

class RubricScorer:
    def __init__(self, rubric_path=None):
        if rubric_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.rubric_path = os.path.join(base_dir, "config", "scoring_rubric.xlsx")
        else:
            self.rubric_path = rubric_path
            
        self._load_rubric()
        
    def _load_rubric(self):
        try:
            self.cat_df = pd.read_excel(self.rubric_path, sheet_name="Category_Weights")
            self.comp_df = pd.read_excel(self.rubric_path, sheet_name="Competitor_Tiers")
            self.sent_df = pd.read_excel(self.rubric_path, sheet_name="Sentiment_Multipliers")
            self.key_df = pd.read_excel(self.rubric_path, sheet_name="Keyword_Boosts")
            self.decay_df = pd.read_excel(self.rubric_path, sheet_name="Time_Decay")
            
            # Precompute fast lookups
            self.cat_weights = dict(zip(self.cat_df['Category'].str.lower(), self.cat_df['Points']))
            self.ui_maps = dict(zip(self.cat_df['Category'].str.lower(), self.cat_df['UI_Tab_Mapping']))
            
            # Competitors could be multiple separated by commas. We'll handle matching in the scorer.
            self.comp_weights = dict(zip(self.comp_df['Competitor_Name'].str.lower(), self.comp_df['Points']))
            
            self.sent_weights = dict(zip(self.sent_df['Scenario'].str.lower(), self.sent_df['Points']))
            self.key_weights = dict(zip(self.key_df['Keyword'].str.lower(), self.key_df['Points']))
            
            # Sort decay by age to easily find the multiplier
            self.decay_df = self.decay_df.sort_values(by="Age_In_Days")
        except Exception as e:
            print(f"Error loading rubric {self.rubric_path}: {e}")
            self.cat_weights = {}
            self.ui_maps = {}
            self.comp_weights = {}
            self.sent_weights = {}
            self.key_weights = {}
            self.decay_df = pd.DataFrame(columns=["Age_In_Days", "Multiplier"])

    def get_dynamic_categories(self):
        """Returns the list of categories currently defined in the rubric to inject into the LLM prompt."""
        if hasattr(self, 'cat_df') and not self.cat_df.empty:
            return self.cat_df['Category'].tolist()
        return ["General Industry News"]
        
    def get_ui_mapping(self, category):
        return self.ui_maps.get(str(category).lower(), "Overview")
        
    def _calculate_decay(self, pub_date):
        if not pub_date or pd.isna(pub_date):
            return 1.0
            
        try:
            if isinstance(pub_date, str):
                from dateutil import parser
                d = parser.parse(pub_date, fuzzy=True).replace(tzinfo=None)
            else:
                d = pub_date.replace(tzinfo=None)
                
            days_old = (datetime.now() - d).days
            days_old = max(0, days_old)
            
            multiplier = 1.0
            for _, row in self.decay_df.iterrows():
                if days_old >= row["Age_In_Days"]:
                    multiplier = row["Multiplier"]
                else:
                    break
            return multiplier
        except Exception as e:
            return 1.0

    def calculate_score(self, category, sentiment, title, competitor, pub_date, is_own_brand=False):
        score = 0
        
        # 1. Category Weight
        cat_lower = str(category).lower()
        score += self.cat_weights.get(cat_lower, 0)
        
        # 2. Competitor Weight
        comp_lower = str(competitor).lower()
        comp_score = 0
        for comp, pts in self.comp_weights.items():
            if comp in comp_lower:
                comp_score = max(comp_score, pts)
        score += comp_score
        
        # 3. Sentiment Multiplier
        sent_lower = str(sentiment).lower()
        if is_own_brand:
            if sent_lower == "negative":
                score += self.sent_weights.get("negative_opportunity", 0)
        else:
            if sent_lower == "positive":
                score += self.sent_weights.get("positive_threat", 0)
            elif sent_lower == "negative":
                score += self.sent_weights.get("negative_opportunity", 0)
                
        # 4. Keyword Boosts
        title_lower = str(title).lower()
        for kw, pts in self.key_weights.items():
            if kw in title_lower:
                score += pts
                
        # 5. Time Decay
        multiplier = self._calculate_decay(pub_date)
        
        final_score = int(score * multiplier)
        return min(100, final_score) # Cap at 100
