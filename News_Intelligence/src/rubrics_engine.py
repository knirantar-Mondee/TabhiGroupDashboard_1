import re
import pandas as pd
from src.utils import logger, clean_text

class ArticleData:
    """Encapsulates article fields for evaluation."""
    def __init__(self, title, body):
        self.title = title or ""
        self.body = body or ""
        # Clean and combine text once to avoid repeating cleanup
        self.text_normalized = clean_text(self.title) + " " + clean_text(self.body)


class RubricRule:
    """Represents a single scoring rubric rule from the spreadsheet."""
    def __init__(self, row_dict):
        self.id = str(row_dict.get("Rubric ID", "")).strip()
        self.name = str(row_dict.get("Rubric Name", "")).strip()
        self.pillar = str(row_dict.get("Pillar", "")).strip()
        
        # Handle points safely
        try:
            self.max_points = int(row_dict.get("Max Points", 0))
        except (ValueError, TypeError):
            self.max_points = 0
            
        self.group_id = str(row_dict.get("Group ID", "")).strip()
        if pd.isna(row_dict.get("Group ID")) or self.group_id.lower() == 'nan':
            self.group_id = ""
            
        self.selection_rule = str(row_dict.get("Selection Rule", "")).strip().upper()
        
        # Parse list of anchors & keywords
        self.anchors = self._parse_list(row_dict.get("Required Anchors"))
        self.keywords = self._parse_list(row_dict.get("Supporting Keywords"))

    def _parse_list(self, val):
        if pd.isna(val) or not str(val).strip() or str(val).lower() == 'nan':
            return []
        # Split by comma and clean
        return [item.strip().lower() for item in str(val).split(",") if item.strip()]

    def matches(self, article: ArticleData) -> bool:
        """Checks if the article matches required anchors and supporting keywords."""
        if not self.anchors:
            return False
            
        # 1. Check Required Anchors (Must match at least one)
        anchor_match = any(
            re.search(r'\b' + re.escape(anchor) + r'\b', article.text_normalized)
            for anchor in self.anchors
        )
        if not anchor_match:
            return False
            
        # 2. Check Supporting Keywords (If present, must match at least one)
        if self.keywords:
            return any(
                re.search(r'\b' + re.escape(keyword) + r'\b', article.text_normalized)
                for keyword in self.keywords
            )
            
        return True


class PrecedenceGroup:
    """Manages mutually-exclusive rule execution in a category."""
    def __init__(self, group_id, selection_rule):
        self.group_id = group_id
        self.selection_rule = selection_rule  # 'SINGLE' or 'MULTI'

    def filter_matches(self, triggered_rules: list) -> list:
        """Applies mutual exclusivity rules (e.g. keeping only highest score for SINGLE rule)."""
        group_matches = [r for r in triggered_rules if r.group_id == self.group_id]
        if not group_matches:
            return []
            
        if self.selection_rule == "SINGLE":
            # Return only the single rule with the maximum points in this group
            highest_rule = max(group_matches, key=lambda r: r.max_points)
            return [highest_rule]
            
        # For MULTI or general rules, keep all matches
        return group_matches


class RubricsScoringEngine:
    """Coordinates spreadsheet loading, rule execution, and scoring."""
    def __init__(self, rubrics_excel_path):
        self.rules = []
        self.precedence_groups = {}
        self.path = rubrics_excel_path
        self._load_rubrics()

    def _load_rubrics(self):
        """Loads and parses rules from Excel dynamically."""
        try:
            df = pd.read_excel(self.path, sheet_name="80 Detailed Rubrics")
            for _, row in df.iterrows():
                # Skip rows that don't have Rubric ID
                row_dict = row.to_dict()
                if pd.isna(row_dict.get("Rubric ID")) or not str(row_dict.get("Rubric ID")).strip():
                    continue
                    
                rule = RubricRule(row_dict)
                self.rules.append(rule)
                
                # Organize rules into precedence groups dynamically
                g_id = rule.group_id
                if g_id and g_id not in self.precedence_groups:
                    self.precedence_groups[g_id] = PrecedenceGroup(g_id, rule.selection_rule)
            logger.info(f"Successfully compiled {len(self.rules)} rules and {len(self.precedence_groups)} groups from {self.path}")
        except Exception as e:
            logger.error(f"Failed to load rubrics from {self.path}: {e}")

    def evaluate_article(self, title, body) -> dict:
        """Evaluates an article and returns its score, tier, and matched rule IDs."""
        article = ArticleData(title, body)
        
        # 1. Identify all matching rules
        all_triggered = [rule for rule in self.rules if rule.matches(article)]
        
        # 2. Apply group precedence filtering
        final_matched_rules = []
        
        # Run precedence filters for grouped rules
        processed_group_ids = set()
        for rule in all_triggered:
            g_id = rule.group_id
            if g_id:
                if g_id not in processed_group_ids:
                    group_filter = self.precedence_groups[g_id]
                    final_matched_rules.extend(group_filter.filter_matches(all_triggered))
                    processed_group_ids.add(g_id)
            else:
                # Standalone rules without groups are kept directly
                final_matched_rules.append(rule)
                
        # 3. Sum final points
        total_score = sum(rule.max_points for rule in final_matched_rules)
        total_score = min(total_score, 100)  # Capped at 100
        
        # 4. Map to Tiers
        if total_score >= 75:
            tier = "Tier 1 - Critical"
        elif total_score >= 55:
            tier = "Tier 2 - High"
        elif total_score >= 35:
            tier = "Tier 3 - Standard"
        else:
            tier = "Tier 4 - Low"
            
        return {
            "score": total_score,
            "tier": tier,
            "matched_rules": [r.id for r in final_matched_rules]
        }
