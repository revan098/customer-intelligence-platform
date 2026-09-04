from pathlib import Path
from datetime import datetime
import os
import json
import math

from dotenv import load_dotenv
from google import genai


# ============================================================
# PROJECT PATHS & ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
)

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")


# ============================================================
# VALIDATION
# ============================================================

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is not configured. "
        "Check your .env file."
    )


# ============================================================
# REPORTING IMPORTS
# ============================================================

from src.reporting import (
    get_executive_kpis,
    get_monthly_revenue,
    get_monthly_revenue_detail,
    get_rfm_segments,
    get_customer_countries,
    get_country_revenue,
    get_product_revenue,
    get_product_quantity,
    get_churn_model_summary,
    get_churn_training_summary,
    get_churn_feature_statistics,
    get_churn_risk_distribution,
    get_high_risk_customers,
)


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# REPORT CONFIGURATION
# ============================================================

REPORT_START_DATE = "2009-12-01"
REPORT_END_DATE = "2011-12-09"

CURRENCY = "GBP"
CURRENCY_SYMBOL = "£"

CHURN_LOW_THRESHOLD = 0.50
CHURN_HIGH_THRESHOLD = 0.75


# ============================================================
# DATA CONVERSION HELPERS
# ============================================================

def clean_value(value):
    """
    Convert pandas/numpy/date values into JSON-safe values.
    """

    # None
    if value is None:
        return None

    # pandas / numpy scalar
    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass

    # datetime / timestamp
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass

    # NaN / infinity
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None

    return value


def normalize_data(data):
    """
    Normalize reporting.py outputs.

    Supported:
        - pandas DataFrame
        - dict
        - list
        - tuple
        - scalar values

    This is necessary because functions in reporting.py
    do not all return the same Python type.
    """

    if data is None:
        return None

    # --------------------------------------------------------
    # DataFrame
    # --------------------------------------------------------

    if hasattr(data, "to_dict") and hasattr(data, "columns"):

        records = data.to_dict(
            orient="records"
        )

        return [
            {
                str(key): clean_value(value)
                for key, value in record.items()
            }
            for record in records
        ]

    # --------------------------------------------------------
    # Dictionary
    # --------------------------------------------------------

    if isinstance(data, dict):

        return {
            str(key): clean_value(value)
            for key, value in data.items()
        }

    # --------------------------------------------------------
    # List / Tuple
    # --------------------------------------------------------

    if isinstance(data, (list, tuple)):

        return [
            normalize_data(item)
            for item in data
        ]

    # --------------------------------------------------------
    # Scalar
    # --------------------------------------------------------

    return clean_value(data)


def safe_json(data):
    """
    Convert normalized data to readable JSON.
    """

    normalized = normalize_data(data)

    return json.dumps(
        normalized,
        indent=2,
        ensure_ascii=False,
        default=str,
    )


# ============================================================
# COLLECT VERIFIED BUSINESS DATA
# ============================================================

def collect_report_data():
    """
    Collect verified metrics from the existing reporting layer.

    Gemini receives ONLY this verified reporting data.
    """

    print(
        "Collecting verified business metrics..."
    )

    # --------------------------------------------------------
    # Executive KPIs
    # --------------------------------------------------------

    executive_kpis = get_executive_kpis()

    # --------------------------------------------------------
    # Revenue
    # --------------------------------------------------------

    monthly_revenue = get_monthly_revenue()

    monthly_revenue_detail = (
        get_monthly_revenue_detail()
    )

    # --------------------------------------------------------
    # Customer Segmentation
    # --------------------------------------------------------

    rfm_segments = get_rfm_segments()

    customer_countries = (
        get_customer_countries()
    )

    country_revenue = get_country_revenue()

    # --------------------------------------------------------
    # Products
    # --------------------------------------------------------

    product_revenue = get_product_revenue(
        limit=20
    )

    product_quantity = get_product_quantity(
        limit=20
    )

    # --------------------------------------------------------
    # Churn
    # --------------------------------------------------------

    churn_model_summary = (
        get_churn_model_summary()
    )

    churn_training_summary = (
        get_churn_training_summary()
    )

    churn_feature_statistics = (
        get_churn_feature_statistics()
    )

    churn_risk_distribution = (
        get_churn_risk_distribution()
    )

    high_risk_customers = (
        get_high_risk_customers(
            limit=20
        )
    )

    # --------------------------------------------------------
    # Build verified report package
    # --------------------------------------------------------

    report_data = {

        "report_metadata": {
            "analysis_period_start":
                REPORT_START_DATE,

            "analysis_period_end":
                REPORT_END_DATE,

            "currency":
                CURRENCY,

            "currency_symbol":
                CURRENCY_SYMBOL,

            "data_source":
                "Customer Intelligence MySQL "
                "reporting layer",
        },

        "executive_kpis":
            normalize_data(executive_kpis),

        "monthly_revenue":
            normalize_data(monthly_revenue),

        "monthly_revenue_detail":
            normalize_data(
                monthly_revenue_detail
            ),

        "rfm_segments":
            normalize_data(rfm_segments),

        "customer_countries":
            normalize_data(
                customer_countries
            ),

        "country_revenue":
            normalize_data(
                country_revenue
            ),

        "product_revenue":
            normalize_data(
                product_revenue
            ),

        "product_quantity":
            normalize_data(
                product_quantity
            ),

        "churn_model_summary":
            normalize_data(
                churn_model_summary
            ),

        "churn_training_summary":
            normalize_data(
                churn_training_summary
            ),

        "churn_feature_statistics":
            normalize_data(
                churn_feature_statistics
            ),

        "churn_risk_distribution":
            normalize_data(
                churn_risk_distribution
            ),

        "high_risk_customers":
            normalize_data(
                high_risk_customers
            ),
    }

    print(
        "Verified business data collected."
    )

    return report_data


# ============================================================
# GEMINI PROMPT
# ============================================================

def build_prompt(report_data):
    """
    Build a controlled, evidence-grounded Gemini prompt.
    """

    data_json = safe_json(
        report_data
    )

    prompt = f"""
You are a senior Business Intelligence analyst preparing an
executive Customer Intelligence report.

Analyze ONLY the verified business data provided at the end
of this prompt.

============================================================
REPORT CONTEXT
============================================================

Analysis period:
{REPORT_START_DATE} to {REPORT_END_DATE}

Currency:
British pounds sterling (GBP)

Currency symbol:
£

All monetary values are already in GBP.

IMPORTANT:

- Always use £.
- NEVER use $.
- NEVER convert the currency.
- NEVER estimate currency conversion.

============================================================
DATA-GROUNDING RULES
============================================================

1. Use ONLY the supplied verified data.

2. NEVER invent:
   - numbers
   - percentages
   - customer counts
   - revenue
   - probabilities
   - dates
   - products
   - business causes
   - operational explanations

3. If information is unavailable, explicitly state that it is
   unavailable in the supplied dataset.

4. Every quantitative statement must be supported by the
   supplied data or be a straightforward calculation from it.

5. Do not create statistics that are not present in the data.

============================================================
CAUSALITY RULE
============================================================

Do NOT confuse correlation or association with causation.

For example:

BAD:
"Low product diversity causes churn."

GOOD:
"Lower product diversity is associated with higher observed
churn risk in this dataset."

Do not claim that a particular customer behavior directly causes
churn unless causal evidence is explicitly provided.

============================================================
IDENTIFIER PROTECTION
============================================================

The dataset contains different identifiers.

Customer ID:
Identifies a customer.

Stock Code:
Identifies a product/item.

Invoice:
Identifies an order/invoice.

NEVER change one identifier into another.

CRITICAL EXAMPLE:

Stock Code 23843

MUST be described as:

"Stock Code 23843"

or:

"the product with Stock Code 23843"

NEVER write:

"Customer 23843"

unless the supplied data explicitly identifies 23843 as a customer ID.

Similarly, never describe a Customer ID as a Stock Code.

============================================================
CHURN DEFINITIONS
============================================================

Observed Historical Churn:
The historical active/churned label from the modeling dataset.

Predicted Churn Risk:
The probability generated by the XGBoost machine learning model.

These are different concepts.

Never mix observed churn with predicted risk.

============================================================
EXACT CHURN RISK THRESHOLDS
============================================================

LOW:
probability < 0.50

MEDIUM:
probability >= 0.50 AND < 0.75

HIGH:
probability >= 0.75

Use these exact boundaries.

Therefore:

50.00% = MEDIUM

75.00% = HIGH

Do not change these definitions.

============================================================
BUSINESS INTERPRETATION RULES
============================================================

You may identify meaningful patterns in the supplied data.

However, do not invent explanations.

For example:

If a country has high revenue from a small number of customers,
you may say:

"Revenue is highly concentrated among a small number of
customers in this market."

You may NOT automatically conclude:

- B2B customers
- wholesale customers
- distributors
- commercial accounts
- freight requirements
- logistics problems

unless the supplied data explicitly supports those claims.

If appropriate, recommend further investigation into customer
type or account structure.

============================================================
RECOMMENDATION RULES
============================================================

Recommendations must be:

- practical
- evidence-based
- directly connected to the supplied data
- realistic for a BI/customer analytics team

Do NOT invent arbitrary campaign windows.

For example, do NOT automatically recommend:

"second purchase within 30 days"

unless the supplied data specifically supports 30 days.

Instead:

"Use historical order-gap behavior to determine an appropriate
second-purchase intervention window."

Recommendations are suggestions, not guaranteed outcomes.

============================================================
MACHINE LEARNING INTERPRETATION
============================================================

The XGBoost model is predictive.

Do not say:

"The model proves the customer will churn."

Instead say:

"The model identifies customers whose observed behavioral
profiles are associated with higher predicted churn probability."

A predicted probability is NOT certainty.

============================================================
REPORT STRUCTURE
============================================================

Generate the report using EXACTLY these major sections:

# Customer Intelligence Executive Report

## Executive Summary

Provide 4–6 concise executive insights.

Cover:
- total revenue
- order/customer activity
- strongest RFM segment
- important geographic pattern
- observed historical churn
- predicted churn risk

Only use verified metrics.

---

## Revenue Intelligence

### Financial & Transaction Metrics

Include:
- total revenue
- total orders
- units sold
- AOV
- customer base
- analysis period

### Country-Level Performance

Highlight important markets.

Be careful when customer populations are very small.

Use "revenue concentration" rather than unsupported B2B/wholesale
claims.

### Product-Level Performance

Highlight:
- top revenue items
- high-volume products
- operational/fee-related items where relevant
- notable transaction anomalies

Remember:
Stock Code identifies a product/item.

---

## Customer Segmentation

Explain the six RFM segments:

- Champions
- Potential Loyalists
- At Risk
- Lost / Inactive
- Loyal Customers
- New / Promising

Discuss relevant:
- customer counts
- revenue
- recency
- frequency
- monetary value

Provide evidence-based strategic implications.

---

## Churn Intelligence

### Observed Historical Churn

Include:
- evaluated population
- active customers
- churned customers
- historical churn rate

### Active vs Churned Behavior

Discuss differences in:
- recency
- frequency
- monetary value
- unique products
- tenure

Use association/correlation language.

### Machine Learning Predicted Churn Risk

Include:
- XGBoost
- accuracy
- precision
- recall
- F1
- ROC-AUC
- LOW/MEDIUM/HIGH counts
- average probability by risk tier

Use the exact thresholds provided above.

### High-Risk Customer Profiles

Highlight selected high-risk customers where useful.

Preserve Customer IDs exactly.

Do not confuse Customer IDs with Stock Codes.

---

## Recommended Actions

Provide 4–5 prioritized actions.

For each action include:

1. Action
2. Evidence
3. Target group

Potential themes include:

- Champion retention
- At-Risk reactivation
- High-risk customer prioritization
- Second-purchase conversion
- Product/country investigation

Do not claim B2B or wholesale status without evidence.

---

## Management Questions

Provide 4–5 management questions focused on information not
available in the current dataset.

Possible areas:

- profitability
- COGS
- acquisition channels
- customer type
- operational costs
- large-order context
- reasons for inactivity

Clearly distinguish missing information from observed facts.

============================================================
FINAL QUALITY CONTROL
============================================================

Before producing the final answer, silently perform these checks.

CHECK 1:
All monetary values use £.

CHECK 2:
No $ symbol appears anywhere in the report.

CHECK 3:
Every quantitative statement is supported by supplied data.

CHECK 4:
No invented customer IDs.

CHECK 5:
No invented stock codes.

CHECK 6:
Stock Code and Customer ID are never confused.

CHECK 7:
Churn thresholds are exactly:

LOW < 50%

MEDIUM >= 50% and < 75%

HIGH >= 75%

CHECK 8:
Observed churn and predicted risk are clearly separated.

CHECK 9:
No causal claims.

CHECK 10:
No unsupported B2B/wholesale/distributor claims.

CHECK 11:
No unsupported logistics or operational explanations.

CHECK 12:
No arbitrary campaign windows such as 30 days.

CHECK 13:
No invented profitability or margin information.

CHECK 14:
Recommendations are tied to evidence.

CHECK 15:
If information is unavailable, explicitly state that it is
unavailable.

============================================================
VERIFIED BUSINESS DATA
============================================================

{data_json}

============================================================
FINAL OUTPUT
============================================================

Return ONLY the final executive report in Markdown.

Do not include:

- reasoning
- prompt analysis
- JSON
- code
- external citations
- discussion of being an AI

Make the report professional, concise, factual, and executive-friendly.
"""


    return prompt


# ============================================================
# GENERATE AI REPORT
# ============================================================

def generate_ai_report(report_data):
    """
    Generate the executive report using Gemini.
    """

    print(
        "Generating executive report with Gemini..."
    )

    prompt = build_prompt(
        report_data
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    if response is None:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    report_text = getattr(
        response,
        "text",
        None
    )

    if not report_text:
        raise RuntimeError(
            "Gemini response did not contain report text."
        )

    print(
        "Gemini report generated."
    )

    return report_text.strip()


# ============================================================
# SAVE REPORT
# ============================================================

def save_report(report_text):
    """
    Save generated report as Markdown.
    """

    reports_dir = BASE_DIR / "reports"

    reports_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    report_path = (
        reports_dir
        / f"customer_intelligence_report_{timestamp}.md"
    )

    report_path.write_text(
        report_text,
        encoding="utf-8"
    )

    return report_path


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_genai_reporting_pipeline():

    print("=" * 60)
    print(
        "GEMINI GENAI REPORTING PIPELINE"
    )
    print("=" * 60)

    print(
        f"Gemini model: {GEMINI_MODEL}"
    )

    print(
        f"MySQL host: {MYSQL_HOST}"
    )

    print(
        f"MySQL user configured: "
        f"{bool(MYSQL_USER)}"
    )

    print(
        f"MySQL database: {MYSQL_DATABASE}"
    )

    print()

    # --------------------------------------------------------
    # STEP 1
    # --------------------------------------------------------

    report_data = (
        collect_report_data()
    )

    # --------------------------------------------------------
    # STEP 2
    # --------------------------------------------------------

    report_text = (
        generate_ai_report(
            report_data
        )
    )

    # --------------------------------------------------------
    # STEP 3
    # --------------------------------------------------------

    report_path = save_report(
        report_text
    )

    print()

    print(
        "Report saved to:"
    )

    print(
        report_path
    )

    print()

    print(
        "GEMINI REPORTING PIPELINE COMPLETED."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_genai_reporting_pipeline()