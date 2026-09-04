import sys
import os
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


# ============================================================
# IMPORT PROJECT MODULES
# ============================================================

from src.predict import (
    predict_customer_churn,
    get_customer_profile,
    get_purchase_history,
    get_customer_purchase_trend,
)

from src.reporting import (
    get_executive_kpis,
    get_monthly_revenue,
    get_rfm_segments,
    get_churn_distribution,
    get_country_revenue,
    get_product_revenue,
    get_product_quantity,
    get_monthly_revenue_detail,
    get_churn_model_summary,
    get_churn_feature_statistics,
    get_churn_risk_customers,
    get_churn_training_summary,
    get_all_churn_predictions,
    get_churn_risk_distribution,
    get_high_risk_customers,
)

from src.genai_report import run_genai_reporting_pipeline


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Customer Intelligence Platform",
    page_icon="▦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# THEME STATE (Light / Dark)
# Presentation layer only — analytics workflow unchanged.
# ============================================================

if "ci_theme" not in st.session_state:
    st.session_state.ci_theme = "Light"


def _theme_palette(theme: str) -> dict:
    """
    Returns the CSS variable palette for the selected theme.
    Design ratio: ~20% green accent surfaces, ~80% neutral
    (white for Light / near-black for Dark) surfaces.
    Text colors are always chosen for strong contrast against
    their background (black-ish text on light/white surfaces).
    """

    if theme == "Dark":
        return {
            "bg": "#0F1613",
            "surface": "#161F1B",
            "surface-alt": "#1B2620",
            "primary": "#3FA97A",
            "primary-dark": "#2E7D5B",
            "primary-soft": "#1D2E26",
            "text": "#F1F5F3",
            "text-on-light": "#1F2937",
            "muted": "#9CA8A2",
            "border": "#2A3630",
            "danger": "#E07A7A",
            "warning": "#E0B25C",
            "success": "#3FA97A",
            "shadow": "0 1px 3px rgba(0, 0, 0, 0.35)",
        }

    # Light theme (default) — white-dominant with green accents
    return {
        "bg": "#FFFFFF",
        "surface": "#FFFFFF",
        "surface-alt": "#EAF5EE",
        "primary": "#2E7D5B",
        "primary-dark": "#1F5C43",
        "primary-soft": "#E8F3ED",
        "text": "#1F2937",
        "text-on-light": "#1F2937",
        "muted": "#6B7280",
        "border": "#E5E7EB",
        "danger": "#C94A4A",
        "warning": "#B7791F",
        "success": "#2E7D5B",
        "shadow": "0 1px 2px rgba(31, 41, 55, 0.03)",
    }


PALETTE = _theme_palette(st.session_state.ci_theme)


# ============================================================
# ENTERPRISE UI / UX THEME
# Presentation layer only — analytics workflow unchanged.
# ============================================================

st.markdown(
    f"""
    <style>
    :root {{
        --bg: {PALETTE["bg"]};
        --surface: {PALETTE["surface"]};
        --surface-alt: {PALETTE["surface-alt"]};
        --primary: {PALETTE["primary"]};
        --primary-dark: {PALETTE["primary-dark"]};
        --primary-soft: {PALETTE["primary-soft"]};
        --text: {PALETTE["text"]};
        --text-on-light: {PALETTE["text-on-light"]};
        --muted: {PALETTE["muted"]};
        --border: {PALETTE["border"]};
        --danger: {PALETTE["danger"]};
        --warning: {PALETTE["warning"]};
        --success: {PALETTE["success"]};
    }}

    html, body, [class*="css"] {{
        font-family: "Inter", "Segoe UI", -apple-system, BlinkMacSystemFont,
            "Helvetica Neue", Arial, sans-serif;
    }}

    .stApp {{
        background: var(--bg);
        color: var(--text);
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}

    [data-testid="stSidebar"] {{
        background: var(--surface-alt);
        border-right: 1px solid var(--border);
    }}

    [data-testid="stSidebar"] * {{
        color: var(--text) !important;
    }}

    [data-testid="stSidebar"] > div:first-child {{
        padding-top: 1.5rem;
    }}

    [data-testid="stSidebar"] .stRadio > label {{
        color: var(--muted) !important;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.45rem;
    }}

    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] {{
        gap: 0.25rem;
    }}

    [data-testid="stSidebar"] .stRadio label {{
        border-radius: 8px;
        padding: 0.55rem 0.7rem;
        transition: background 0.15s ease;
    }}

    [data-testid="stSidebar"] .stRadio label:hover {{
        background: var(--primary-soft);
    }}

    [data-testid="stSidebar"] .stCaption {{
        color: var(--muted) !important;
    }}

    h1 {{
        color: var(--primary-dark) !important;
        font-size: 2rem !important;
        font-weight: 750 !important;
        letter-spacing: -0.025em;
        margin-bottom: 0.25rem !important;
    }}

    h2, h3, h4 {{
        color: var(--text) !important;
        font-weight: 700 !important;
        letter-spacing: -0.015em;
    }}

    p, li, span, label {{
        color: var(--text);
    }}

    .block-container {{
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }}

    hr {{
        border: none !important;
        border-top: 1px solid var(--border) !important;
        margin: 1.35rem 0 !important;
    }}

    /* KPI cards */
    [data-testid="stMetric"] {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1rem 1.1rem;
        min-height: 105px;
        box-shadow: {PALETTE["shadow"]};
    }}

    [data-testid="stMetricLabel"] {{
        color: var(--muted) !important;
        font-size: 0.78rem !important;
        font-weight: 650 !important;
    }}

    [data-testid="stMetricValue"] {{
        color: var(--primary-dark) !important;
        font-size: 1.55rem !important;
        font-weight: 750 !important;
    }}

    /* Chart/table containers */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        border-color: var(--border) !important;
        border-radius: 10px !important;
    }}

    [data-testid="stDataFrame"] {{
        border: 1px solid var(--border);
        border-radius: 8px;
        overflow: hidden;
        background: var(--surface);
    }}

    /* Force readable text inside dataframes / tables (always light cells) */
    [data-testid="stDataFrame"] * {{
        color: var(--text-on-light) !important;
    }}

    /* Buttons */
    .stButton > button,
    .stDownloadButton > button {{
        border-radius: 7px;
        font-weight: 650;
        min-height: 42px;
        border: 1px solid var(--primary);
        color: var(--text);
        background: var(--surface);
    }}

    .stButton > button[kind="primary"],
    .stDownloadButton > button[kind="primary"] {{
        background: var(--primary);
        color: #FFFFFF !important;
    }}

    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button[kind="primary"]:hover {{
        background: var(--primary-dark);
        border-color: var(--primary-dark);
    }}

    /* Inputs */
    .stTextInput input,
    .stNumberInput input,
    .stSelectbox div[data-baseweb="select"] > div {{
        border-radius: 7px;
        border-color: var(--border);
        background: var(--surface);
        color: var(--text) !important;
    }}

    /* Status messages — restrained enterprise look, readable text */
    [data-testid="stAlert"] {{
        border-radius: 8px;
    }}

    [data-testid="stAlert"] p {{
        color: var(--text-on-light) !important;
    }}

    /* Progress bars */
    [data-testid="stProgressBar"] > div > div {{
        background: var(--primary);
    }}

    /* Sidebar brand */
    .ci-brand {{
        padding: 0.2rem 0 0.9rem 0;
    }}

    .ci-brand-title {{
        color: var(--primary-dark) !important;
        font-size: 1.12rem;
        font-weight: 800;
        letter-spacing: -0.015em;
    }}

    .ci-brand-subtitle {{
        color: var(--muted) !important;
        font-size: 0.76rem;
        line-height: 1.45;
        margin-top: 0.25rem;
    }}

    .ci-page-kicker {{
        color: var(--primary);
        font-size: 0.75rem;
        font-weight: 750;
        letter-spacing: 0.10em;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }}

    /* Semantic risk cards */
    .risk-card {{
        border-radius: 9px;
        padding: 0.85rem 1rem;
        background: var(--surface);
        border: 1px solid var(--border);
        margin-bottom: 0.55rem;
    }}

    .risk-high {{
        border-left: 4px solid var(--danger);
    }}

    .risk-medium {{
        border-left: 4px solid var(--warning);
    }}

    .risk-low {{
        border-left: 4px solid var(--success);
    }}

    .risk-label {{
        font-size: 0.76rem;
        font-weight: 750;
        letter-spacing: 0.06em;
    }}

    .risk-value {{
        color: var(--text);
        font-size: 1.05rem;
        font-weight: 700;
        margin-top: 0.15rem;
    }}

    /* Remove excess Streamlit top spacing on radio */
    [data-testid="stSidebar"] .stMarkdown {{
        margin-bottom: 0.2rem;
    }}

    /* Theme toggle segment */
    [data-testid="stSidebar"] div[role="radiogroup"][aria-label="theme-toggle"] {{
        flex-direction: row;
        gap: 0.4rem;
    }}

    @media (max-width: 900px) {{
        .block-container {{
            padding-left: 1rem;
            padding-right: 1rem;
        }}
        h1 {{
            font-size: 1.65rem !important;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_currency(value):
    return f"£{value:,.2f}"


def format_number(value):
    return f"{value:,.0f}"


def format_percentage(value):
    return f"{value * 100:.2f}%"


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    """
    <div class="ci-brand">
        <div class="ci-brand-title">Customer Intelligence</div>
        <div class="ci-brand-subtitle">
            Customer Intelligence &amp;<br>
            Automated Reporting Platform
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

theme_choice = st.sidebar.radio(
    "Appearance",
    ["Light", "Dark"],
    index=0 if st.session_state.ci_theme == "Light" else 1,
    horizontal=True,
    key="ci_theme_radio",
    label_visibility="collapsed",
)

if theme_choice != st.session_state.ci_theme:
    st.session_state.ci_theme = theme_choice
    st.rerun()

st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    [
        "Executive Overview",
        "Revenue Intelligence",
        "Churn Intelligence",
        "Customer 360",
        "AI Executive Report",
    ],
)

st.sidebar.divider()

st.sidebar.caption(
    "Retail Analytics Platform"
)

st.sidebar.caption(
    "Python • MySQL • XGBoost • SHAP • Streamlit"
)


# ============================================================
# PAGE 1 — EXECUTIVE OVERVIEW
# ============================================================

if page == "Executive Overview":

    st.title("Executive Overview")

    st.markdown(
        """
        ### Customer Intelligence & Business Performance

        Monitor revenue, customer activity, RFM segments, and
        observed churn across the retail customer base.
        """
    )

    st.divider()

    try:

        kpis = get_executive_kpis()

    except Exception as e:

        st.error(
            f"Unable to load executive KPIs: {e}"
        )

        st.stop()

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Total Revenue",
            format_currency(
                kpis["total_revenue"]
            ),
        )

    with col2:

        st.metric(
            "Total Customers",
            format_number(
                kpis["total_customers"]
            ),
        )

    with col3:

        st.metric(
            "Total Orders",
            format_number(
                kpis["total_orders"]
            ),
        )

    col4, col5, col6 = st.columns(3)

    with col4:

        st.metric(
            "Average Order Value",
            format_currency(
                kpis["average_order_value"]
            ),
        )

    with col5:

        st.metric(
            "Observed Churn Rate",
            format_percentage(
                kpis["churn_rate"]
            ),
        )

    with col6:

        st.metric(
            "Churned Customers",
            format_number(
                kpis["churned_customers"]
            ),
        )

    st.divider()

    # --------------------------------------------------------
    # MONTHLY REVENUE
    # --------------------------------------------------------

    st.subheader("Monthly Revenue")

    try:

        monthly_revenue = get_monthly_revenue()

        if monthly_revenue.empty:

            st.warning(
                "No monthly revenue data available."
            )

        else:

            chart_data = monthly_revenue.copy()

            chart_data["month"] = pd.to_datetime(
                chart_data["month"]
            )

            chart_data = chart_data.set_index(
                "month"
            )

            st.line_chart(
                chart_data["revenue"]
            )

    except Exception as e:

        st.error(
            f"Unable to load monthly revenue: {e}"
        )

    st.divider()

    # --------------------------------------------------------
    # RFM SEGMENTS
    # --------------------------------------------------------

    st.subheader("Customer Segmentation")

    try:

        rfm_segments = get_rfm_segments()

        if rfm_segments.empty:

            st.warning(
                "No RFM segment data available."
            )

        else:

            col1, col2 = st.columns(2)

            with col1:

                st.markdown(
                    "#### Customers by Segment"
                )

                customer_chart = (
                    rfm_segments
                    .set_index("segment")[
                        ["customers"]
                    ]
                )

                st.bar_chart(
                    customer_chart
                )

            with col2:

                st.markdown(
                    "#### Revenue by Segment"
                )

                revenue_chart = (
                    rfm_segments
                    .set_index("segment")[
                        ["revenue"]
                    ]
                )

                st.bar_chart(
                    revenue_chart
                )

            st.markdown(
                "#### RFM Segment Summary"
            )

            display_rfm = rfm_segments.copy()

            display_rfm["revenue"] = (
                display_rfm["revenue"]
                .map(
                    lambda x: f"£{x:,.2f}"
                )
            )

            display_rfm["customers"] = (
                display_rfm["customers"]
                .map(
                    lambda x: f"{x:,}"
                )
            )

            st.dataframe(
                display_rfm,
                use_container_width=True,
                hide_index=True,
            )

    except Exception as e:

        st.error(
            f"Unable to load RFM segments: {e}"
        )

    st.divider()

    # --------------------------------------------------------
    # CHURN DISTRIBUTION
    # --------------------------------------------------------

    st.subheader(
        "Customer Churn Distribution"
    )

    try:

        churn_distribution = (
            get_churn_distribution()
        )

        if churn_distribution.empty:

            st.warning(
                "No churn distribution data available."
            )

        else:

            col1, col2 = st.columns(2)

            with col1:

                st.markdown(
                    "#### Active vs Churned"
                )

                churn_chart = (
                    churn_distribution
                    .set_index("status")[
                        ["customers"]
                    ]
                )

                st.bar_chart(
                    churn_chart
                )

            with col2:

                st.markdown(
                    "#### Churn Summary"
                )

                for _, row in (
                    churn_distribution.iterrows()
                ):

                    status = row["status"]

                    customers = int(
                        row["customers"]
                    )

                    if status == "Churned":

                        st.error(
                            f"{status}: "
                            f"{customers:,}"
                        )

                    else:

                        st.success(
                            f"{status}: "
                            f"{customers:,}"
                        )

                st.metric(
                    "Observed Churn Rate",
                    format_percentage(
                        kpis["churn_rate"]
                    ),
                )

    except Exception as e:

        st.error(
            f"Unable to load churn distribution: {e}"
        )


# ============================================================
# PAGE 2 — REVENUE INTELLIGENCE
# ============================================================

elif page == "Revenue Intelligence":

    st.title("Revenue Intelligence")

    st.markdown(
        """
        ### Revenue, Product & Geographic Performance

        Analyze revenue trends, customer contribution, product
        performance, and country-level business activity.
        """
    )

    st.divider()

    try:

        kpis = get_executive_kpis()

        monthly_detail = (
            get_monthly_revenue_detail()
        )

        country_revenue = (
            get_country_revenue()
        )

        product_revenue = (
            get_product_revenue()
        )

        product_quantity = (
            get_product_quantity()
        )

    except Exception as e:

        st.error(
            f"Unable to load revenue intelligence data: {e}"
        )

        st.stop()

    # ========================================================
    # REVENUE KPIs
    # ========================================================

    st.subheader("Revenue Performance")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Total Revenue",
            format_currency(
                kpis["total_revenue"]
            ),
        )

    with col2:

        st.metric(
            "Total Orders",
            format_number(
                kpis["total_orders"]
            ),
        )

    with col3:

        st.metric(
            "Average Order Value",
            format_currency(
                kpis["average_order_value"]
            ),
        )

    with col4:

        if not monthly_detail.empty:

            total_quantity = (
                monthly_detail["quantity"]
                .sum()
            )

        else:

            total_quantity = 0

        st.metric(
            "Total Quantity",
            format_number(
                total_quantity
            ),
        )

    st.divider()

    # ========================================================
    # MONTHLY REVENUE TREND
    # ========================================================

    st.subheader("Monthly Revenue Trend")

    if monthly_detail.empty:

        st.warning(
            "No monthly revenue data available."
        )

    else:

        revenue_chart = (
            monthly_detail[
                [
                    "month",
                    "revenue",
                ]
            ]
            .copy()
        )

        revenue_chart["month"] = (
            pd.to_datetime(
                revenue_chart["month"]
            )
        )

        revenue_chart = (
            revenue_chart
            .set_index("month")
        )

        st.line_chart(
            revenue_chart["revenue"]
        )

    # --------------------------------------------------------
    # MONTHLY ORDERS + CUSTOMERS
    # --------------------------------------------------------

    if not monthly_detail.empty:

        col1, col2 = st.columns(2)

        with col1:

            st.markdown(
                "#### Monthly Orders"
            )

            order_chart = (
                monthly_detail[
                    [
                        "month",
                        "orders",
                    ]
                ]
                .copy()
            )

            order_chart["month"] = (
                pd.to_datetime(
                    order_chart["month"]
                )
            )

            order_chart = (
                order_chart
                .set_index("month")
            )

            st.line_chart(
                order_chart["orders"]
            )

        with col2:

            st.markdown(
                "#### Monthly Customers"
            )

            customer_chart = (
                monthly_detail[
                    [
                        "month",
                        "customers",
                    ]
                ]
                .copy()
            )

            customer_chart["month"] = (
                pd.to_datetime(
                    customer_chart["month"]
                )
            )

            customer_chart = (
                customer_chart
                .set_index("month")
            )

            st.line_chart(
                customer_chart["customers"]
            )

    st.divider()

    # ========================================================
    # REVENUE INSIGHTS
    # ========================================================

    st.subheader("Revenue Insights")

    if not monthly_detail.empty:

        highest_revenue_month = (
            monthly_detail.loc[
                monthly_detail["revenue"].idxmax()
            ]
        )

        highest_order_month = (
            monthly_detail.loc[
                monthly_detail["orders"].idxmax()
            ]
        )

        col1, col2 = st.columns(2)

        with col1:

            st.info(
                f"""
                **Highest Revenue Month**

                {highest_revenue_month["month"].strftime("%B %Y")}

                Revenue:
                **£{highest_revenue_month["revenue"]:,.2f}**
                """
            )

        with col2:

            st.info(
                f"""
                **Highest Order Month**

                {highest_order_month["month"].strftime("%B %Y")}

                Orders:
                **{int(highest_order_month["orders"]):,}**
                """
            )

    st.divider()

    # ========================================================
    # COUNTRY INTELLIGENCE
    # ========================================================

    st.subheader(
        "Geographic Revenue Intelligence"
    )

    if country_revenue.empty:

        st.warning(
            "No country revenue data available."
        )

    else:

        col1, col2 = st.columns(2)

        with col1:

            st.markdown(
                "#### Top Countries by Revenue"
            )

            top_countries = (
                country_revenue
                .head(10)
                .set_index("country")[
                    ["revenue"]
                ]
            )

            st.bar_chart(
                top_countries
            )

        with col2:

            st.markdown(
                "#### Top Countries by Customers"
            )

            top_customer_countries = (
                country_revenue
                .sort_values(
                    "customers",
                    ascending=False
                )
                .head(10)
                .set_index("country")[
                    ["customers"]
                ]
            )

            st.bar_chart(
                top_customer_countries
            )

        st.markdown(
            "#### Country Performance"
        )

        country_table = (
            country_revenue.copy()
        )

        country_table["revenue"] = (
            country_table["revenue"]
            .map(
                lambda x: f"£{x:,.2f}"
            )
        )

        country_table["customers"] = (
            country_table["customers"]
            .map(
                lambda x: f"{int(x):,}"
            )
        )

        country_table["orders"] = (
            country_table["orders"]
            .map(
                lambda x: f"{int(x):,}"
            )
        )

        country_table["quantity"] = (
            country_table["quantity"]
            .map(
                lambda x: f"{int(x):,}"
            )
        )

        st.dataframe(
            country_table,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # ========================================================
    # PRODUCT INTELLIGENCE
    # ========================================================

    st.subheader(
        "Product Intelligence"
    )

    st.markdown(
        "#### Top 20 Products by Revenue"
    )

    if product_revenue.empty:

        st.warning(
            "No product revenue data available."
        )

    else:

        product_revenue_chart = (
            product_revenue
            .head(10)
            .copy()
        )

        product_revenue_chart["product"] = (
            product_revenue_chart[
                "stock_code"
            ].astype(str)
            + " — "
            + product_revenue_chart[
                "description"
            ]
            .fillna("Unknown Product")
            .astype(str)
            .str.slice(0, 40)
        )

        product_revenue_chart = (
            product_revenue_chart
            .set_index("product")[
                ["revenue"]
            ]
        )

        st.bar_chart(
            product_revenue_chart
        )

        product_revenue_table = (
            product_revenue.copy()
        )

        product_revenue_table["revenue"] = (
            product_revenue_table["revenue"]
            .map(
                lambda x: f"£{x:,.2f}"
            )
        )

        product_revenue_table["quantity"] = (
            product_revenue_table["quantity"]
            .map(
                lambda x: f"{int(x):,}"
            )
        )

        product_revenue_table["orders"] = (
            product_revenue_table["orders"]
            .map(
                lambda x: f"{int(x):,}"
            )
        )

        st.dataframe(
            product_revenue_table,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown(
        "#### Top 20 Products by Quantity Sold"
    )

    if product_quantity.empty:

        st.warning(
            "No product quantity data available."
        )

    else:

        product_quantity_chart = (
            product_quantity
            .head(10)
            .copy()
        )

        product_quantity_chart["product"] = (
            product_quantity_chart[
                "stock_code"
            ].astype(str)
            + " — "
            + product_quantity_chart[
                "description"
            ]
            .fillna("Unknown Product")
            .astype(str)
            .str.slice(0, 40)
        )

        product_quantity_chart = (
            product_quantity_chart
            .set_index("product")[
                ["quantity"]
            ]
        )

        st.bar_chart(
            product_quantity_chart
        )

        product_quantity_table = (
            product_quantity.copy()
        )

        product_quantity_table["quantity"] = (
            product_quantity_table["quantity"]
            .map(
                lambda x: f"{int(x):,}"
            )
        )

        product_quantity_table["orders"] = (
            product_quantity_table["orders"]
            .map(
                lambda x: f"{int(x):,}"
            )
        )

        product_quantity_table["revenue"] = (
            product_quantity_table["revenue"]
            .map(
                lambda x: f"£{x:,.2f}"
            )
        )

        st.dataframe(
            product_quantity_table,
            use_container_width=True,
            hide_index=True,
        )

    # ========================================================
    # BUSINESS TAKEAWAYS
    # ========================================================

    st.divider()

    st.subheader(
        "Business Takeaways"
    )

    if not country_revenue.empty:

        top_country = (
            country_revenue.iloc[0]
        )

        st.write(
            f"""
            **Leading Country:**  
            {top_country["country"]} generated the highest
            customer-attributed revenue at
            **£{top_country["revenue"]:,.2f}**.
            """
        )

    if not product_revenue.empty:

        top_product = (
            product_revenue.iloc[0]
        )

        st.write(
            f"""
            **Leading Product:**  
            Product **{top_product["stock_code"]}**
            generated the highest revenue at
            **£{top_product["revenue"]:,.2f}**.
            """
        )

    if not product_quantity.empty:

        top_quantity_product = (
            product_quantity.iloc[0]
        )

        st.write(
            f"""
            **Highest Volume Product:**  
            Product **{top_quantity_product["stock_code"]}**
            recorded the highest quantity sold:
            **{int(top_quantity_product["quantity"]):,} units**.
            """
        )

    st.caption(
        "Revenue intelligence is based on the cleaned sales "
        "transactions stored in MySQL."
    )


# ============================================================
# PAGE 3 — CHURN INTELLIGENCE
# ============================================================

elif page == "Churn Intelligence":

    st.title("Churn Intelligence")

    st.markdown(
        """
        ### Predictive Customer Retention Analysis

        Identify customers at risk of churn, understand the
        behavioral differences between active and churned customers,
        and prioritize customers for retention campaigns.
        """
    )

    st.divider()

    # ========================================================
    # LOAD CHURN DATA
    # ========================================================

    try:

        churn_summary = (
            get_churn_model_summary()
        )

        risk_distribution = (
            get_churn_risk_distribution()
        )

        feature_statistics = (
            get_churn_feature_statistics()
        )

        high_risk_customers = (
            get_high_risk_customers(
                limit=20
            )
        )

    except Exception as e:

        st.error(
            f"Unable to load churn intelligence data: {e}"
        )

        st.stop()

    # ========================================================
    # CHURN KPIs
    # ========================================================

    st.subheader(
        "Churn Overview"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Model Population",
            format_number(
                churn_summary[
                    "total_customers"
                ]
            ),
        )

    with col2:

        st.metric(
            "Churned Customers",
            format_number(
                churn_summary[
                    "churned_customers"
                ]
            ),
        )

    with col3:

        st.metric(
            "Active Customers",
            format_number(
                churn_summary[
                    "active_customers"
                ]
            ),
        )

    with col4:

        st.metric(
            "Observed Churn Rate",
            format_percentage(
                churn_summary[
                    "churn_rate"
                ]
            ),
        )

    st.caption(
        "Observed churn rate is based on the historical churn labels. "
        "Model population refers to customers with pre-cutoff "
        "behavioral features."
    )

    st.divider()

    # ========================================================
    # MODEL RISK DISTRIBUTION
    # ========================================================

    st.subheader(
        "Predicted Churn Risk Distribution"
    )

    if risk_distribution.empty:

        st.warning(
            "No churn risk predictions available."
        )

    else:

        col1, col2 = st.columns(2)

        with col1:

            risk_chart = (
                risk_distribution
                .set_index("risk_level")[
                    ["customers"]
                ]
            )

            st.bar_chart(
                risk_chart
            )

        with col2:

            st.markdown(
                "#### Risk Summary"
            )

            total_predicted = (
                risk_distribution[
                    "customers"
                ].sum()
            )

            for _, row in (
                risk_distribution.iterrows()
            ):

                risk = row[
                    "risk_level"
                ]

                customers = int(
                    row["customers"]
                )

                percentage = (
                    customers
                    / total_predicted
                    if total_predicted > 0
                    else 0
                )

                if risk == "HIGH":

                    st.error(
                        f"HIGH: "
                        f"{customers:,} customers "
                        f"({percentage:.1%})"
                    )

                elif risk == "MEDIUM":

                    st.warning(
                        f"MEDIUM: "
                        f"{customers:,} customers "
                        f"({percentage:.1%})"
                    )

                else:

                    st.success(
                        f"LOW: "
                        f"{customers:,} customers "
                        f"({percentage:.1%})"
                    )

    st.divider()

    # ========================================================
    # ACTIVE VS CHURNED BEHAVIOR
    # ========================================================

    st.subheader(
        "Active vs Churned Customer Behavior"
    )

    if feature_statistics.empty:

        st.warning(
            "No churn feature statistics available."
        )

    else:

        comparison = (
            feature_statistics
            .set_index("status")
        )

        col1, col2 = st.columns(2)

        with col1:

            st.markdown(
                "#### Average Recency"
            )

            st.bar_chart(
                comparison[
                    ["avg_recency"]
                ]
            )

            st.markdown(
                "#### Average Frequency"
            )

            st.bar_chart(
                comparison[
                    ["avg_frequency"]
                ]
            )

            st.markdown(
                "#### Average Monetary Value"
            )

            st.bar_chart(
                comparison[
                    ["avg_monetary_value"]
                ]
            )

        with col2:

            st.markdown(
                "#### Average Product Diversity"
            )

            st.bar_chart(
                comparison[
                    ["avg_unique_products"]
                ]
            )

            st.markdown(
                "#### Average Quantity"
            )

            st.bar_chart(
                comparison[
                    ["avg_quantity"]
                ]
            )

            st.markdown(
                "#### Average Customer Tenure"
            )

            st.bar_chart(
                comparison[
                    ["avg_tenure"]
                ]
            )

    st.divider()

    # ========================================================
    # BEHAVIOR COMPARISON TABLE
    # ========================================================

    st.subheader(
        "Behavioral Comparison"
    )

    if not feature_statistics.empty:

        comparison_table = (
            feature_statistics[
                [
                    "status",
                    "customers",
                    "avg_recency",
                    "avg_frequency",
                    "avg_monetary_value",
                    "avg_order_value",
                    "avg_unique_products",
                    "avg_quantity",
                    "avg_order_gap",
                    "avg_tenure",
                ]
            ]
            .copy()
        )

        comparison_table = (
            comparison_table
            .rename(
                columns={
                    "status": "Status",
                    "customers": "Customers",
                    "avg_recency": "Avg Recency",
                    "avg_frequency": "Avg Frequency",
                    "avg_monetary_value": "Avg Monetary Value",
                    "avg_order_value": "Avg Order Value",
                    "avg_unique_products": "Avg Unique Products",
                    "avg_quantity": "Avg Quantity",
                    "avg_order_gap": "Avg Order Gap",
                    "avg_tenure": "Avg Tenure",
                }
            )
        )

        st.dataframe(
            comparison_table,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # ========================================================
    # HIGH-RISK CUSTOMERS
    # ========================================================

    st.subheader(
        "Highest-Priority Customers"
    )

    st.markdown(
        """
        These customers have the highest predicted probability
        of churn according to the saved XGBoost model.
        """
    )

    if high_risk_customers.empty:

        st.warning(
            "No high-risk customers found."
        )

    else:

        display_risk = (
            high_risk_customers[
                [
                    "customer_id",
                    "churn_probability",
                    "risk_level",
                    "recency_days",
                    "frequency",
                    "monetary_value",
                    "average_order_value",
                    "unique_products",
                ]
            ]
            .copy()
        )

        display_risk[
            "churn_probability"
        ] = (
            display_risk[
                "churn_probability"
            ] * 100
        ).map(
            lambda x: f"{x:.2f}%"
        )

        display_risk[
            "monetary_value"
        ] = (
            display_risk[
                "monetary_value"
            ].map(
                lambda x: f"£{x:,.2f}"
            )
        )

        display_risk[
            "average_order_value"
        ] = (
            display_risk[
                "average_order_value"
            ].map(
                lambda x: f"£{x:,.2f}"
            )
        )

        display_risk = (
            display_risk
            .rename(
                columns={
                    "customer_id": "Customer ID",
                    "churn_probability": "Churn Probability",
                    "risk_level": "Risk",
                    "recency_days": "Recency (Days)",
                    "frequency": "Orders",
                    "monetary_value": "Revenue",
                    "average_order_value": "AOV",
                    "unique_products": "Unique Products",
                }
            )
        )

        st.dataframe(
            display_risk,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # ========================================================
    # RETENTION OPPORTUNITY
    # ========================================================

    st.subheader(
        "Retention Opportunity"
    )

    high_risk_count = 0

    if not risk_distribution.empty:

        high_rows = risk_distribution[
            risk_distribution["risk_level"]
            == "HIGH"
        ]

        if not high_rows.empty:

            high_risk_count = int(
                high_rows.iloc[0]["customers"]
            )

    st.warning(
        f"""
        **{high_risk_count:,} customers** are currently classified
        as HIGH churn risk by the XGBoost model.

        These customers should be prioritized for targeted
        retention or reactivation campaigns.
        """
    )

    st.info(
        """
        **Recommended workflow:**

        1. Prioritize high-probability customers.
        2. Review Customer 360 profiles.
        3. Understand the behavioral drivers using SHAP.
        4. Select an appropriate retention strategy.
        5. Track customer response after intervention.
        """
    )

    st.divider()

    st.caption(
        "Model: XGBoost | Prediction population: 5,281 customers | "
        "Explainability: SHAP | Data source: MySQL"
    )


# ============================================================
# PAGE 4 — CUSTOMER 360
# ============================================================

elif page == "Customer 360":

    st.title("Customer 360")

    st.markdown(
        """
        Analyze an individual customer's purchasing behavior,
        churn probability, model explanations, and purchase history.
        """
    )

    st.divider()

    # --------------------------------------------------------
    # CUSTOMER INPUT
    # --------------------------------------------------------

    customer_id = st.number_input(
        "Enter Customer ID",
        min_value=1,
        step=1,
        value=17008,
    )

    analyze_button = st.button(
        "Analyze Customer",
        type="primary",
        use_container_width=True,
    )

    if analyze_button:

        # ====================================================
        # CUSTOMER PROFILE
        # ====================================================

        profile = get_customer_profile(
            customer_id
        )

        if profile is None:

            st.error(
                f"Customer {customer_id} "
                "was not found in the churn feature table."
            )

            st.stop()

        # ====================================================
        # CHURN PREDICTION
        # ====================================================

        with st.spinner(
            "Running churn prediction..."
        ):

            result = predict_customer_churn(
                customer_id
            )

        if result is None:

            st.error(
                "Unable to generate churn prediction."
            )

            st.stop()

        # ====================================================
        # CHURN SUMMARY
        # ====================================================

        st.subheader(
            "Churn Risk"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Churn Probability",
                f"{result['churn_probability'] * 100:.2f}%",
            )

        with col2:

            st.metric(
                "Risk Level",
                result["risk_level"],
            )

        with col3:

            prediction_text = (
                "Likely to Churn"
                if result["prediction"] == 1
                else "Likely to Stay"
            )

            st.metric(
                "Prediction",
                prediction_text,
            )

        # ----------------------------------------------------
        # RISK MESSAGE
        # ----------------------------------------------------

        if result["risk_level"] == "HIGH":

            st.error(
                "HIGH RISK — "
                "This customer should be prioritized "
                "for retention or reactivation."
            )

        elif result["risk_level"] == "MEDIUM":

            st.warning(
                "MEDIUM RISK — "
                "This customer may benefit from "
                "targeted engagement."
            )

        else:

            st.success(
                "LOW RISK — "
                "No immediate retention intervention "
                "is required."
            )

        st.divider()

        # ====================================================
        # CUSTOMER PROFILE
        # ====================================================

        st.subheader(
            "Customer Profile"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Recency",
                f"{profile['recency_days']} days",
            )

        with col2:

            st.metric(
                "Orders",
                f"{profile['frequency']:,}",
            )

        with col3:

            st.metric(
                "Revenue",
                f"£{profile['monetary_value']:,.2f}",
            )

        with col4:

            st.metric(
                "Average Order Value",
                f"£{profile['average_order_value']:,.2f}",
            )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Unique Products",
                f"{profile['unique_products']:,}",
            )

        with col2:

            st.metric(
                "Total Quantity",
                f"{profile['total_quantity']:,.0f}",
            )

        with col3:

            if profile["average_order_gap"] is None:

                gap_value = "N/A"

            else:

                gap_value = (
                    f"{profile['average_order_gap']:.1f} days"
                )

            st.metric(
                "Average Order Gap",
                gap_value,
            )

        with col4:

            st.metric(
                "Customer Tenure",
                f"{profile['customer_tenure_days']} days",
            )

        st.divider()

        # ====================================================
        # MODEL EXPLANATION
        # ====================================================

        st.subheader(
            "Why is this customer at risk?"
        )

        col1, col2 = st.columns(2)

        # ----------------------------------------------------
        # CHURN DRIVERS
        # ----------------------------------------------------

        with col1:

            st.markdown(
                "### Top Churn Drivers"
            )

            drivers = result[
                "churn_drivers"
            ]

            if drivers.empty:

                st.info(
                    "No positive churn drivers found."
                )

            else:

                for _, row in drivers.iterrows():

                    feature = row["feature"]
                    shap_value = row["shap_value"]
                    feature_value = row[
                        "feature_value"
                    ]

                    if pd.isna(feature_value):

                        value_text = "N/A"

                    else:

                        value_text = (
                            f"{feature_value:.2f}"
                        )

                    st.write(
                        f"**{feature}**"
                    )

                    st.caption(
                        f"Value: {value_text} | "
                        f"SHAP impact: "
                        f"+{shap_value:.3f}"
                    )

                    st.progress(
                        min(
                            abs(float(shap_value)),
                            1.0,
                        )
                    )

        # ----------------------------------------------------
        # PROTECTIVE FACTORS
        # ----------------------------------------------------

        with col2:

            st.markdown(
                "### Protective Factors"
            )

            protective = result[
                "protective_factors"
            ]

            if protective.empty:

                st.info(
                    "No protective factors identified."
                )

            else:

                for _, row in protective.iterrows():

                    feature = row["feature"]
                    shap_value = row["shap_value"]
                    feature_value = row[
                        "feature_value"
                    ]

                    if pd.isna(feature_value):

                        value_text = "N/A"

                    else:

                        value_text = (
                            f"{feature_value:.2f}"
                        )

                    st.write(
                        f"**{feature}**"
                    )

                    st.caption(
                        f"Value: {value_text} | "
                        f"SHAP impact: "
                        f"{shap_value:.3f}"
                    )

                    st.progress(
                        min(
                            abs(float(shap_value)),
                            1.0,
                        )
                    )

        st.divider()

        # ====================================================
        # RECOMMENDATION
        # ====================================================

        st.subheader(
            "Recommended Business Action"
        )

        st.info(
            result["recommendation"]
        )

        st.divider()

        # ====================================================
        # PURCHASE HISTORY
        # ====================================================

        st.subheader(
            "Recent Purchase History"
        )

        purchase_history = (
            get_purchase_history(
                customer_id,
                limit=20,
            )
        )

        if purchase_history.empty:

            st.info(
                "No purchase history available."
            )

        else:

            display_history = (
                purchase_history.copy()
            )

            display_history["invoice_date"] = (
                pd.to_datetime(
                    display_history[
                        "invoice_date"
                    ]
                ).dt.strftime(
                    "%Y-%m-%d %H:%M"
                )
            )

            display_history["price"] = (
                display_history["price"]
                .map(
                    lambda x: f"£{x:,.2f}"
                )
            )

            display_history["revenue"] = (
                display_history["revenue"]
                .map(
                    lambda x: f"£{x:,.2f}"
                )
            )

            st.dataframe(
                display_history,
                use_container_width=True,
                hide_index=True,
            )

        st.divider()

        # ====================================================
        # PURCHASE TREND
        # ====================================================

        st.subheader(
            "Customer Purchase Trend"
        )

        purchase_trend = (
            get_customer_purchase_trend(
                customer_id
            )
        )

        if purchase_trend.empty:

            st.info(
                "No purchase trend data available."
            )

        else:

            trend = purchase_trend.copy()

            trend["month"] = pd.to_datetime(
                trend["month"]
            )

            trend = trend.set_index(
                "month"
            )

            st.markdown(
                "#### Monthly Revenue"
            )

            st.line_chart(
                trend["revenue"]
            )

            st.markdown(
                "#### Monthly Orders"
            )

            st.line_chart(
                trend["orders"]
            )

        st.divider()

        st.caption(
            "Model: XGBoost | Explainability: SHAP | "
            "Data source: MySQL"
        )


# ============================================================
# PAGE 5 — AI EXECUTIVE REPORT
# ============================================================

elif page == "AI Executive Report":

    st.title("AI Executive Report")

    st.markdown(
        """
        ### Gemini-Powered Business Reporting

        Generate a management-ready executive report from the verified
        business metrics already stored in MySQL and analyzed by the
        Customer Intelligence Platform.
        """
    )

    st.divider()

    reports_dir = BASE_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    def get_report_files():
        return sorted(
            reports_dir.glob("customer_intelligence_report_*.md"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

    report_files = get_report_files()
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("AI Model", model_name)

    with col2:
        st.metric("Available Reports", f"{len(report_files):,}")

    with col3:
        if report_files:
            generated_text = datetime.fromtimestamp(
                report_files[0].stat().st_mtime
            ).strftime("%Y-%m-%d %H:%M")
        else:
            generated_text = "Not generated"

        st.metric("Latest Report", generated_text)

    st.divider()

    st.subheader("Generate AI Report")

    st.write(
        "The report is generated from verified metrics collected by "
        "the existing reporting layer. Gemini turns those metrics "
        "into an executive narrative."
    )

    generate_button = st.button(
        "Generate New Executive Report",
        type="primary",
        use_container_width=True,
    )

    if generate_button:

        if not os.getenv("GEMINI_API_KEY"):
            st.error(
                "GEMINI_API_KEY is not configured. "
                "Check your project's .env file."
            )

        else:

            try:

                with st.spinner(
                    "Collecting verified metrics and generating "
                    "the Gemini executive report..."
                ):
                    run_genai_reporting_pipeline()

                st.success(
                    "AI executive report generated successfully."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Unable to generate the AI executive report: {e}"
                )

    st.divider()
    st.subheader("Latest Executive Report")

    report_files = get_report_files()

    if not report_files:

        st.info(
            "No AI executive report exists yet. "
            "Click 'Generate New Executive Report' above."
        )

    else:

        latest_report = report_files[0]

        try:
            report_content = latest_report.read_text(
                encoding="utf-8"
            )

        except Exception as e:

            st.error(f"Unable to read the latest report: {e}")

        else:

            generated_time = datetime.fromtimestamp(
                latest_report.stat().st_mtime
            ).strftime("%Y-%m-%d %H:%M:%S")

            col1, col2 = st.columns([3, 1])

            with col1:
                st.caption(f"File: {latest_report.name}")

            with col2:
                st.caption(f"Generated: {generated_time}")

            st.markdown(report_content)

            st.divider()

            st.download_button(
                label="Download Report (Markdown)",
                data=report_content,
                file_name=latest_report.name,
                mime="text/markdown",
                use_container_width=True,
            )

            if len(report_files) > 1:

                st.divider()
                st.subheader("Report History")

                history_rows = []

                for report_path in report_files:

                    modified_time = datetime.fromtimestamp(
                        report_path.stat().st_mtime
                    )

                    history_rows.append(
                        {
                            "Report": report_path.name,
                            "Generated": modified_time.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                        }
                    )

                st.dataframe(
                    pd.DataFrame(history_rows),
                    use_container_width=True,
                    hide_index=True,
                )

    st.divider()

    st.caption(
        "AI reporting uses Google Gemini to summarize verified "
        "metrics from the MySQL reporting layer. The generated "
        "narrative does not replace the underlying dashboard metrics."
    )