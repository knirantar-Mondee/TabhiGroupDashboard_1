# Tabhi Group News Intelligence: Rubrics Scoring & Prioritization Spec

This document details the logic, pillars, and calculation mechanics of the dynamic **News Rubrics Scoring Engine (v2)** implemented in the competitive intelligence pipeline.

---

## 1. Core Architecture

The prioritization engine is built to evaluate competitor news dynamically from segment-specific Excel matrices (`MIRAEE_News_Rubrics.xlsx`, `MONDEE_News_Rubrics.xlsx`, `ABHEE_News_Rubrics.xlsx`) at runtime. This allows business teams to adjust scoring rules, keyword weights, and thresholds inside the spreadsheets without requiring any codebase modifications.

```
                  +--------------------------------+
                  |  Competitor News Article Feed  |
                  +---------------+----------------+
                                  |
                                  v
                  +---------------+----------------+
                  |   Article Text Normalization   |
                  +---------------+----------------+
                                  |
                                  v
                  +---------------+----------------+
                  |     Rubric Engine Loader       |
                  |  (Compiles spreadsheet rules)  |
                  +---------------+----------------+
                                  |
                                  v
                  +---------------+----------------+
                  |     Anchor/Keyword Match       |
                  |     (re.search word bounds)    |
                  +---------------+----------------+
                                  |
                                  v
                  +---------------+----------------+
                  |  Precedence Group Filtering    |
                  | (Applies SINGLE/MULTI rules)   |
                  +---------------+----------------+
                                  |
                                  v
                  +---------------+----------------+
                  |     Sum & Cap Points (0-100)   |
                  +---------------+----------------+
                                  |
                                  v
                  +---------------+----------------+
                  |     Priority Tier Mapping      |
                  +--------------------------------+
```

---

## 2. The Three Rubric Pillars

Evaluation rules are grouped under three strategic dimensions:

### A. Strategic Intent (SI)
Evaluates the competitor's long-term corporate direction. Matches items like:
- Mergers and Acquisitions (M&A)
- Funding rounds (Venture Capital, Private Equity)
- IPO preparations and listings
- C-suite executive shakeups

### B. Execution Momentum (EM)
Measures the velocity of the competitor's operational activities. Matches items like:
- Capital investment brackets (e.g. raised amount size scales)
- Scale of regional expansion
- Regulatory approvals and legal disputes

### C. Competitive Impact (CI)
Measures the direct threat level of competitor moves against Tabhi Group brands. Matches items like:
- Competitor tier classification (Core, Spend/FinOps, Tech Leader, New Entrant)
- Feature releases and product line overlap (e.g., Expense tools, AI booking agents)
- Market share penetration and target geographic focus

---

## 3. Calculation & Precedence Rules

### A. Individual Rule Match
For a rubric row to match an article, it must satisfy two conditions:
1. **Required Anchors**: The article title or body **MUST** match at least one keyword listed in the *Required Anchors* column.
2. **Supporting Keywords**: If *Supporting Keywords* are defined, the article **MUST ALSO** match at least one of these keywords.
*Note: All matching is done case-insensitively using word-boundary regular expressions (`\bkeyword\b`).*

### B. Precedence Groups (Mutually Exclusive Rules)
Certain groups enforce mutually-exclusive overrides. If multiple rules inside the same group match, they are resolved as follows:

| Group ID | Category | Selection Rule | Logic |
| :--- | :--- | :---: | :--- |
| **`G_COMP_TIER`** | Competitor Tier | **SINGLE** | Keeps only the single competitor tier with the highest score (e.g., Navan core competitor override). |
| **`G_PRODUCT_OVERLAP`** | Product Feature Overlaps | **SINGLE** | Keeps only the highest product overlap match (e.g., Agentic travel over simple expense tools). |
| **`G_EVENT_PRIORITY`** | Funding / Corporate Events | **SINGLE** | Keeps only the highest scoring corporate event. |
| **`G_FUND_STRENGTH`** | Execution Funding Size | **SINGLE** | Keeps only the highest point-bracket match for funding sizes. |

* **`SINGLE`** rules filter the group results to return only the single rule that yields the maximum points.
* **`MULTI`** rules (or rules without group IDs) are cumulative and sum up together.

### C. Score Sum & Capping
Once precedence filters are applied, the engine sums the `Max Points` of all surviving matched rules:

$$\text{Final Score} = \min\left(\sum \text{Points}_{\text{surviving\_rules}}, 100\right)$$

---

## 4. Priority Tier Mapping

Calculated scores are mapped to four priority bands on the dashboard:

| Tier | Score Range | Dashboard Indicator | Action Required |
| :--- | :---: | :---: | :--- |
| **Tier 1 - Critical** | $\ge$ 75 | Glowing Red Left Border + 🚨 Badge | Immediate executive briefing |
| **Tier 2 - High** | 55 – 74 | Orange Left Border + ⚠️ Badge | Strategy team tracking |
| **Tier 3 - Standard** | 35 – 54 | Standard Card | Logged for routine review |
| **Tier 4 - Low** | < 35 | Standard Card | Background sector volume |

---

## 5. Python Integration Overview

The scoring pipeline is orchestrated by the following core components in `src/rubrics_engine.py`:

* **`ArticleData`**: Normalizes and combines the article title and body once to optimize search performance.
* **`RubricRule`**: Models a single row, compiling keywords and checking rule activations.
* **`PrecedenceGroup`**: Implements the `SINGLE` highest-weight filtering rule.
* **`RubricsScoringEngine`**: Coordinates sheet loading, evaluates rules, aggregates scores, and assigns priority tiers.

### How to Modify Rules
To alter scoring weights, add new competitors, or add new keywords:
1. Open the segment rubrics sheet (e.g. `MIRAEE_News_Rubrics.xlsx`).
2. Navigate to the **`80 Detailed Rubrics`** tab.
3. Edit, insert, or remove rows. Ensure `Rubric ID`, `Max Points`, `Required Anchors`, `Group ID`, and `Selection Rule` columns are filled.
4. Save and commit the Excel file. The scraper pipeline will immediately load the updated rules on its next automated run.
