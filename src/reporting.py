from pathlib import Path

import pandas as pd

from src.database import engine


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# EXECUTIVE KPIs
# ============================================================

def get_executive_kpis():
    """
    Return executive-level business KPIs.

    Business metrics come from customer-identified transactions.
    Churn metrics come from the churn modeling population.
    """

    transaction_query = """
    SELECT
        COUNT(DISTINCT customer_id) AS total_customers,
        COUNT(DISTINCT invoice) AS total_orders,
        SUM(quantity) AS total_quantity,
        SUM(revenue) AS total_revenue,

        CASE
            WHEN COUNT(DISTINCT invoice) > 0
            THEN SUM(revenue) / COUNT(DISTINCT invoice)
            ELSE 0
        END AS average_order_value,

        MIN(invoice_date) AS first_transaction_date,
        MAX(invoice_date) AS last_transaction_date

    FROM transactions

    WHERE customer_id IS NOT NULL
    """

    transaction_df = pd.read_sql(
        transaction_query,
        engine
    )

    churn_query = """
    SELECT
        COUNT(*) AS model_population,
        SUM(churned) AS churned_customers,
        SUM(
            CASE
                WHEN churned = 0 THEN 1
                ELSE 0
            END
        ) AS active_customers,
        AVG(churned) AS churn_rate

    FROM customer_churn_modeling
    """

    churn_df = pd.read_sql(
        churn_query,
        engine
    )

    if transaction_df.empty:
        return {
            "total_customers": 0,
            "total_orders": 0,
            "total_quantity": 0,
            "total_revenue": 0.0,
            "average_order_value": 0.0,
            "churn_rate": 0.0,
            "churned_customers": 0,
            "active_customers": 0,
            "first_transaction_date": None,
            "last_transaction_date": None,
        }

    row = transaction_df.iloc[0]

    churn_rate = 0.0
    churned_customers = 0
    active_customers = 0

    if not churn_df.empty:
        churn_row = churn_df.iloc[0]

        churn_rate = float(
            churn_row["churn_rate"]
        )

        churned_customers = int(
            churn_row["churned_customers"]
        )

        active_customers = int(
            churn_row["active_customers"]
        )

    return {
        "total_customers": int(
            row["total_customers"]
        ),

        "total_orders": int(
            row["total_orders"]
        ),

        "total_quantity": int(
            row["total_quantity"]
        ),

        "total_revenue": float(
            row["total_revenue"]
        ),

        "average_order_value": float(
            row["average_order_value"]
        ),

        "churn_rate": churn_rate,

        "churned_customers":
            churned_customers,

        "active_customers":
            active_customers,

        "first_transaction_date":
            row["first_transaction_date"],

        "last_transaction_date":
            row["last_transaction_date"],
    }


# ============================================================
# MONTHLY REVENUE
# ============================================================

def get_monthly_revenue():
    """
    Return monthly revenue, orders and customer count.
    """

    query = """
    SELECT
        DATE_FORMAT(
            invoice_date,
            '%%Y-%%m-01'
        ) AS month,

        SUM(revenue) AS revenue,

        COUNT(DISTINCT invoice) AS orders,

        COUNT(DISTINCT customer_id) AS customers

    FROM transactions

    WHERE customer_id IS NOT NULL

    GROUP BY DATE_FORMAT(
        invoice_date,
        '%%Y-%%m-01'
    )

    ORDER BY month
    """

    df = pd.read_sql(
        query,
        engine
    )

    if not df.empty:
        df["month"] = pd.to_datetime(
            df["month"]
        )

    return df


# ============================================================
# MONTHLY REVENUE DETAIL
# ============================================================

def get_monthly_revenue_detail():
    """
    Return detailed monthly business performance.
    """

    query = """
    SELECT
        DATE_FORMAT(
            invoice_date,
            '%%Y-%%m-01'
        ) AS month,

        SUM(revenue) AS revenue,

        COUNT(DISTINCT invoice) AS orders,

        COUNT(DISTINCT customer_id) AS customers,

        SUM(quantity) AS quantity

    FROM transactions

    WHERE customer_id IS NOT NULL

    GROUP BY DATE_FORMAT(
        invoice_date,
        '%%Y-%%m-01'
    )

    ORDER BY month
    """

    df = pd.read_sql(
        query,
        engine
    )

    if not df.empty:
        df["month"] = pd.to_datetime(
            df["month"]
        )

    return df


# ============================================================
# RFM SEGMENTS
# ============================================================

def get_rfm_segments():
    """
    Return RFM customer segment statistics.
    """

    query = """
    SELECT
        customer_segment AS segment,

        COUNT(*) AS customers,

        SUM(monetary_value) AS revenue,

        AVG(recency_days)
            AS avg_recency,

        AVG(frequency)
            AS avg_frequency,

        AVG(monetary_value)
            AS avg_monetary_value,

        AVG(average_order_value)
            AS avg_order_value,

        AVG(unique_products)
            AS avg_unique_products,

        AVG(average_order_gap)
            AS avg_order_gap

    FROM customer_rfm

    GROUP BY customer_segment

    ORDER BY revenue DESC
    """

    return pd.read_sql(
        query,
        engine
    )


# ============================================================
# CUSTOMER COUNTRIES
# ============================================================

def get_customer_countries():
    """
    Return customer count by country.
    """

    query = """
    SELECT
        country,

        COUNT(DISTINCT customer_id)
            AS customers

    FROM customers

    WHERE country IS NOT NULL

    GROUP BY country

    ORDER BY customers DESC
    """

    return pd.read_sql(
        query,
        engine
    )


# ============================================================
# COUNTRY REVENUE
# ============================================================

def get_country_revenue():
    """
    Return revenue performance by country.
    """

    query = """
    SELECT
        country,

        COUNT(DISTINCT customer_id)
            AS customers,

        COUNT(DISTINCT invoice)
            AS orders,

        SUM(quantity)
            AS quantity,

        SUM(revenue)
            AS revenue

    FROM transactions

    WHERE customer_id IS NOT NULL

      AND country IS NOT NULL

    GROUP BY country

    ORDER BY revenue DESC
    """

    return pd.read_sql(
        query,
        engine
    )


# ============================================================
# PRODUCT REVENUE
# ============================================================

def get_product_revenue(limit=20):
    """
    Return top products by revenue.

    Includes order count for Streamlit compatibility.
    """

    query = """
    SELECT
        stock_code,

        description,

        COUNT(DISTINCT invoice)
            AS orders,

        SUM(quantity)
            AS quantity,

        SUM(revenue)
            AS revenue

    FROM transactions

    GROUP BY
        stock_code,
        description

    ORDER BY revenue DESC

    LIMIT %(limit)s
    """

    return pd.read_sql(
        query,
        engine,
        params={
            "limit": int(limit)
        }
    )


# ============================================================
# PRODUCT QUANTITY
# ============================================================

def get_product_quantity(limit=20):
    """
    Return top products by quantity.

    Includes order count for compatibility.
    """

    query = """
    SELECT
        stock_code,

        description,

        COUNT(DISTINCT invoice)
            AS orders,

        SUM(quantity)
            AS quantity,

        SUM(revenue)
            AS revenue

    FROM transactions

    GROUP BY
        stock_code,
        description

    ORDER BY quantity DESC

    LIMIT %(limit)s
    """

    return pd.read_sql(
        query,
        engine,
        params={
            "limit": int(limit)
        }
    )


# ============================================================
# CHURN MODEL SUMMARY
# ============================================================

def get_churn_model_summary():
    """
    Return XGBoost model metrics and churn population.

    Model metrics are from the final selected model evaluation.
    Population metrics are queried dynamically from MySQL.
    """

    query = """
    SELECT
        COUNT(*) AS total_customers,

        SUM(churned)
            AS churned_customers,

        SUM(
            CASE
                WHEN churned = 0
                THEN 1
                ELSE 0
            END
        ) AS active_customers,

        AVG(churned)
            AS churn_rate

    FROM customer_churn_modeling
    """

    df = pd.read_sql(
        query,
        engine
    )

    if df.empty:
        total_customers = 0
        churned_customers = 0
        active_customers = 0
        churn_rate = 0.0

    else:
        row = df.iloc[0]

        total_customers = int(
            row["total_customers"]
        )

        churned_customers = int(
            row["churned_customers"]
        )

        active_customers = int(
            row["active_customers"]
        )

        churn_rate = float(
            row["churn_rate"]
        )

    return {
        # Model
        "model": "XGBoost",

        "accuracy": 0.729423,

        "precision": 0.728467,

        "recall": 0.833055,

        "f1_score": 0.777259,

        "roc_auc": 0.794397,

        # Population
        "total_customers":
            total_customers,

        "churned_customers":
            churned_customers,

        "active_customers":
            active_customers,

        "churn_rate":
            churn_rate,
    }


# ============================================================
# CHURN TRAINING SUMMARY
# ============================================================

def get_churn_training_summary():
    """
    Return churn modeling population statistics.
    """

    query = """
    SELECT
        COUNT(*) AS total_customers,

        SUM(churned)
            AS churned_customers,

        SUM(
            CASE
                WHEN churned = 0
                THEN 1
                ELSE 0
            END
        ) AS active_customers,

        AVG(churned)
            AS churn_rate

    FROM customer_churn_modeling
    """

    df = pd.read_sql(
        query,
        engine
    )

    if df.empty:
        return {
            "total_customers": 0,
            "churned_customers": 0,
            "active_customers": 0,
            "churn_rate": 0.0,
        }

    row = df.iloc[0]

    return {
        "total_customers":
            int(row["total_customers"]),

        "churned_customers":
            int(row["churned_customers"]),

        "active_customers":
            int(row["active_customers"]),

        "churn_rate":
            float(row["churn_rate"]),
    }


# ============================================================
# CHURN FEATURE STATISTICS
# ============================================================

def get_churn_feature_statistics():
    """
    Compare behavioral characteristics of active and churned
    customers.

    Column names are compatible with the existing dashboard.
    """

    query = """
    SELECT

        CASE
            WHEN churned = 1
            THEN 'Churned'
            ELSE 'Active'
        END AS status,

        churned,

        COUNT(*) AS customers,

        AVG(recency_days)
            AS avg_recency,

        AVG(frequency)
            AS avg_frequency,

        AVG(monetary_value)
            AS avg_monetary_value,

        AVG(average_order_value)
            AS avg_order_value,

        AVG(unique_products)
            AS avg_unique_products,

        AVG(total_quantity)
            AS avg_quantity,

        AVG(total_quantity)
            AS avg_total_quantity,

        AVG(average_order_gap)
            AS avg_order_gap,

        AVG(customer_tenure_days)
            AS avg_tenure

    FROM customer_churn_modeling

    GROUP BY churned

    ORDER BY churned
    """

    return pd.read_sql(
        query,
        engine
    )


# ============================================================
# ALL PERSISTED CHURN PREDICTIONS
# ============================================================

def get_all_churn_predictions():
    """
    Read the latest persisted predictions from MySQL.

    The ML model is NOT loaded here.
    Predictions are NOT recalculated here.

    Predictions are generated by:

        python -m src.prediction_pipeline
    """

    query = """
    SELECT
        customer_id,

        churn_probability,

        prediction,

        risk_level,

        prediction_date

    FROM churn_predictions

    ORDER BY churn_probability DESC
    """

    df = pd.read_sql(
        query,
        engine
    )

    if not df.empty:

        df["customer_id"] = (
            df["customer_id"]
            .astype(int)
        )

        df["churn_probability"] = (
            df["churn_probability"]
            .astype(float)
        )

        df["prediction"] = (
            df["prediction"]
            .astype(int)
        )

        df["risk_level"] = (
            df["risk_level"]
            .astype(str)
        )

        df["prediction_date"] = (
            pd.to_datetime(
                df["prediction_date"]
            )
        )

    return df


# ============================================================
# CHURN RISK DISTRIBUTION
# ============================================================

def get_churn_risk_distribution():
    """
    Return persisted churn risk distribution.
    """

    query = """
    SELECT

        risk_level,

        COUNT(*) AS customers,

        AVG(churn_probability)
            AS avg_probability,

        MAX(churn_probability)
            AS max_probability,

        MIN(churn_probability)
            AS min_probability

    FROM churn_predictions

    GROUP BY risk_level

    ORDER BY FIELD(
        risk_level,
        'LOW',
        'MEDIUM',
        'HIGH'
    )
    """

    return pd.read_sql(
        query,
        engine
    )


# Streamlit compatibility
# ============================================================
# CUSTOMER CHURN DISTRIBUTION
# ============================================================

def get_churn_distribution():
    """
    Return actual churn distribution:
    Active vs Churned.

    Used by the Streamlit dashboard.
    """

    query = """
    SELECT
        CASE
            WHEN churned = 1
            THEN 'Churned'
            ELSE 'Active'
        END AS status,

        COUNT(*) AS customers,

        ROUND(
            COUNT(*) * 100.0 /
            (SELECT COUNT(*) FROM customer_churn_modeling),
            2
        ) AS percentage

    FROM customer_churn_modeling

    GROUP BY churned

    ORDER BY churned
    """

    return pd.read_sql(
        query,
        engine
    )


# ============================================================
# CHURN RISK CUSTOMERS
# ============================================================

def get_churn_risk_customers(limit=20):
    """
    Return customers ordered by churn probability.

    Predictions come from churn_predictions.
    Behavioral features come from customer_churn_modeling.
    """

    query = """
    SELECT

        p.customer_id,

        p.churn_probability,

        p.prediction,

        p.risk_level,

        p.prediction_date,

        f.recency_days,

        f.frequency,

        f.monetary_value,

        f.average_order_value,

        f.unique_products,

        f.total_quantity,

        f.average_order_gap,

        f.customer_tenure_days

    FROM churn_predictions p

    INNER JOIN customer_churn_modeling f

        ON p.customer_id = f.customer_id

    ORDER BY
        p.churn_probability DESC

    LIMIT %(limit)s
    """

    df = pd.read_sql(
        query,
        engine,
        params={
            "limit": int(limit)
        }
    )

    if not df.empty:

        df["customer_id"] = (
            df["customer_id"]
            .astype(int)
        )

        df["churn_probability"] = (
            df["churn_probability"]
            .astype(float)
        )

        df["prediction"] = (
            df["prediction"]
            .astype(int)
        )

    return df


# ============================================================
# HIGH-RISK CUSTOMERS
# ============================================================

def get_high_risk_customers(limit=20):
    """
    Return HIGH-risk customers only.
    """

    query = """
    SELECT

        p.customer_id,

        p.churn_probability,

        p.prediction,

        p.risk_level,

        p.prediction_date,

        f.recency_days,

        f.frequency,

        f.monetary_value,

        f.average_order_value,

        f.unique_products,

        f.total_quantity,

        f.average_order_gap,

        f.customer_tenure_days

    FROM churn_predictions p

    INNER JOIN customer_churn_modeling f

        ON p.customer_id = f.customer_id

    WHERE p.risk_level = 'HIGH'

    ORDER BY
        p.churn_probability DESC

    LIMIT %(limit)s
    """

    df = pd.read_sql(
        query,
        engine,
        params={
            "limit": int(limit)
        }
    )

    if not df.empty:

        df["customer_id"] = (
            df["customer_id"]
            .astype(int)
        )

        df["churn_probability"] = (
            df["churn_probability"]
            .astype(float)
        )

        df["prediction"] = (
            df["prediction"]
            .astype(int)
        )

    return df


# ============================================================
# CUSTOMER PROFILE
# ============================================================

def get_customer_profile(customer_id):
    """
    Return basic customer information.
    """

    query = """
    SELECT

        customer_id,

        country,

        first_purchase_date,

        last_purchase_date,

        total_orders,

        total_revenue

    FROM customers

    WHERE customer_id = %(customer_id)s
    """

    df = pd.read_sql(
        query,
        engine,
        params={
            "customer_id": int(customer_id)
        }
    )

    if df.empty:
        return None

    row = df.iloc[0]

    return {
        "customer_id":
            int(row["customer_id"]),

        "country":
            row["country"],

        "first_purchase_date":
            row["first_purchase_date"],

        "last_purchase_date":
            row["last_purchase_date"],

        "total_orders":
            int(row["total_orders"]),

        "total_revenue":
            float(row["total_revenue"]),
    }


# ============================================================
# CUSTOMER FEATURES
# ============================================================

def get_customer_features(customer_id):
    """
    Return detailed customer behavioral features.
    """

    query = """
    SELECT

        customer_id,

        country,

        first_purchase_date,

        last_purchase_date,

        recency_days,

        frequency,

        monetary_value,

        average_order_value,

        unique_products,

        total_quantity,

        average_order_gap,

        customer_tenure_days

    FROM customer_features

    WHERE customer_id = %(customer_id)s
    """

    return pd.read_sql(
        query,
        engine,
        params={
            "customer_id": int(customer_id)
        }
    )


# ============================================================
# CUSTOMER CHURN PREDICTION
# ============================================================

def get_customer_churn_prediction(customer_id):
    """
    Return persisted churn prediction for one customer.
    """

    query = """
    SELECT

        customer_id,

        churn_probability,

        prediction,

        risk_level,

        prediction_date

    FROM churn_predictions

    WHERE customer_id = %(customer_id)s
    """

    df = pd.read_sql(
        query,
        engine,
        params={
            "customer_id": int(customer_id)
        }
    )

    if df.empty:
        return None

    row = df.iloc[0]

    return {
        "customer_id":
            int(row["customer_id"]),

        "churn_probability":
            float(row["churn_probability"]),

        "prediction":
            int(row["prediction"]),

        "risk_level":
            str(row["risk_level"]),

        "prediction_date":
            row["prediction_date"],
    }


# ============================================================
# CUSTOMER PURCHASE HISTORY
# ============================================================

def get_customer_purchase_history(
    customer_id,
    limit=20
):
    """
    Return recent transactions for a customer.
    """

    query = """
    SELECT

        invoice,

        invoice_date,

        stock_code,

        description,

        quantity,

        price,

        revenue

    FROM transactions

    WHERE customer_id = %(customer_id)s

    ORDER BY invoice_date DESC

    LIMIT %(limit)s
    """

    return pd.read_sql(
        query,
        engine,
        params={
            "customer_id": int(customer_id),
            "limit": int(limit),
        }
    )


# Streamlit compatibility
def get_purchase_history(
    customer_id,
    limit=20
):
    """
    Backward-compatible alias.
    """

    return get_customer_purchase_history(
        customer_id,
        limit
    )


# ============================================================
# CUSTOMER PURCHASE TREND
# ============================================================

def get_customer_purchase_trend(customer_id):
    """
    Return monthly customer purchase trend.
    """

    query = """
    SELECT

        DATE_FORMAT(
            invoice_date,
            '%%Y-%%m-01'
        ) AS month,

        COUNT(DISTINCT invoice)
            AS orders,

        SUM(quantity)
            AS quantity,

        SUM(revenue)
            AS revenue

    FROM transactions

    WHERE customer_id = %(customer_id)s

    GROUP BY DATE_FORMAT(
        invoice_date,
        '%%Y-%%m-01'
    )

    ORDER BY month
    """

    df = pd.read_sql(
        query,
        engine,
        params={
            "customer_id": int(customer_id)
        }
    )

    if not df.empty:
        df["month"] = pd.to_datetime(
            df["month"]
        )

    return df


# ============================================================
# CUSTOMER RFM
# ============================================================

def get_customer_rfm(customer_id):
    """
    Return RFM information for one customer.
    """

    query = """
    SELECT

        customer_id,

        recency_days,

        frequency,

        monetary_value,

        average_order_value,

        r_score,

        f_score,

        m_score,

        customer_segment

    FROM customer_rfm

    WHERE customer_id = %(customer_id)s
    """

    df = pd.read_sql(
        query,
        engine,
        params={
            "customer_id": int(customer_id)
        }
    )

    if df.empty:
        return None

    row = df.iloc[0]

    return {
        "customer_id":
            int(row["customer_id"]),

        "recency_days":
            int(row["recency_days"]),

        "frequency":
            int(row["frequency"]),

        "monetary_value":
            float(row["monetary_value"]),

        "average_order_value":
            float(row["average_order_value"]),

        "r_score":
            int(row["r_score"]),

        "f_score":
            int(row["f_score"]),

        "m_score":
            int(row["m_score"]),

        "customer_segment":
            row["customer_segment"],
    }


# ============================================================
# PREDICTION PIPELINE STATUS
# ============================================================

def get_prediction_pipeline_status():
    """
    Return persisted prediction pipeline status.
    """

    query = """
    SELECT

        COUNT(*) AS prediction_count,

        MIN(prediction_date)
            AS earliest_prediction,

        MAX(prediction_date)
            AS latest_prediction

    FROM churn_predictions
    """

    df = pd.read_sql(
        query,
        engine
    )

    if df.empty:
        return {}

    row = df.iloc[0]

    return {
        "prediction_count":
            int(row["prediction_count"]),

        "earliest_prediction":
            row["earliest_prediction"],

        "latest_prediction":
            row["latest_prediction"],
    }


# ============================================================
# PREDICTION COVERAGE VALIDATION
# ============================================================

def validate_prediction_coverage():
    """
    Verify that every customer in the modeling population
    has a persisted churn prediction.
    """

    query = """
    SELECT

        (
            SELECT COUNT(*)
            FROM customer_churn_modeling
        ) AS modeling_customers,

        (
            SELECT COUNT(*)
            FROM churn_predictions
        ) AS prediction_customers,

        (
            SELECT COUNT(*)

            FROM customer_churn_modeling m

            LEFT JOIN churn_predictions p

                ON m.customer_id = p.customer_id

            WHERE p.customer_id IS NULL

        ) AS missing_predictions
    """

    df = pd.read_sql(
        query,
        engine
    )

    if df.empty:
        return {
            "valid": False,
            "modeling_customers": 0,
            "prediction_customers": 0,
            "missing_predictions": 0,
        }

    row = df.iloc[0]

    modeling_customers = int(
        row["modeling_customers"]
    )

    prediction_customers = int(
        row["prediction_customers"]
    )

    missing_predictions = int(
        row["missing_predictions"]
    )

    return {
        "valid": (
            modeling_customers
            == prediction_customers
            and missing_predictions == 0
        ),

        "modeling_customers":
            modeling_customers,

        "prediction_customers":
            prediction_customers,

        "missing_predictions":
            missing_predictions,
    }


# ============================================================
# MODULE VALIDATION
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("REPORTING MODULE VALIDATION")
    print("=" * 60)

    print("\n1. Executive KPIs")

    print(
        get_executive_kpis()
    )

    print("\n2. Churn Model Summary")

    print(
        get_churn_model_summary()
    )

    print("\n3. Prediction Pipeline Status")

    print(
        get_prediction_pipeline_status()
    )

    print("\n4. Prediction Coverage")

    print(
        validate_prediction_coverage()
    )

    print("\n5. Churn Risk Distribution")

    print(
        get_churn_risk_distribution()
    )

    print("\n6. Top Churn Risk Customers")

    print(
        get_churn_risk_customers(10)
    )

    print("\n7. Top High-Risk Customers")

    print(
        get_high_risk_customers(10)
    )

    print("\n" + "=" * 60)
    print(
        "REPORTING MODULE VALIDATION COMPLETED"
    )
    print("=" * 60)