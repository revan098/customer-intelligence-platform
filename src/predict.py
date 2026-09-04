from pathlib import Path

import joblib
import pandas as pd
import shap

from src.database import engine


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "models" / "churn_xgb_pipeline.joblib"


# =========================================================
# LOAD TRAINED MODEL
# =========================================================

model = joblib.load(MODEL_PATH)


# =========================================================
# CREATE SHAP EXPLAINER FROM THE EXACT SAVED MODEL
# =========================================================

# Extract the XGBoost model from the saved pipeline
xgb_model = model.named_steps["model"]

# Create SHAP explainer directly from this exact model
shap_explainer = shap.TreeExplainer(xgb_model)


# =========================================================
# FEATURES USED BY THE MODEL
# =========================================================

FEATURE_COLUMNS = [
    "recency_days",
    "frequency",
    "monetary_value",
    "average_order_value",
    "unique_products",
    "total_quantity",
    "average_order_gap",
    "customer_tenure_days",
]


# =========================================================
# GET CUSTOMER FEATURES FROM MYSQL
# =========================================================

def get_customer_features(customer_id):
    """
    Retrieve churn-model features for one customer from MySQL.
    """

    query = """
    SELECT
        customer_id,
        recency_days,
        frequency,
        monetary_value,
        average_order_value,
        unique_products,
        total_quantity,
        average_order_gap,
        customer_tenure_days
    FROM customer_churn_features
    WHERE customer_id = %(customer_id)s
    """

    df = pd.read_sql(
        query,
        engine,
        params={"customer_id": customer_id}
    )

    return df


# =========================================================
# GET CUSTOMER PROFILE
# =========================================================

def get_customer_profile(customer_id):
    """
    Retrieve customer profile information.
    """

    customer_df = get_customer_features(customer_id)

    if customer_df.empty:
        return None

    row = customer_df.iloc[0]

    return {
        "customer_id": int(row["customer_id"]),

        "recency_days": int(row["recency_days"]),

        "frequency": int(row["frequency"]),

        "monetary_value": float(row["monetary_value"]),

        "average_order_value": float(
            row["average_order_value"]
        ),

        "unique_products": int(
            row["unique_products"]
        ),

        "total_quantity": float(
            row["total_quantity"]
        ),

        "average_order_gap": (
            None
            if pd.isna(row["average_order_gap"])
            else float(row["average_order_gap"])
        ),

        "customer_tenure_days": int(
            row["customer_tenure_days"]
        ),
    }


# =========================================================
# PREDICT CUSTOMER CHURN
# =========================================================

def predict_customer_churn(customer_id):
    """
    Predict churn probability for one customer and return:

    - churn probability
    - prediction
    - risk level
    - SHAP churn drivers
    - SHAP protective factors
    - business recommendation
    """

    # -----------------------------------------------------
    # Retrieve customer data
    # -----------------------------------------------------

    customer_df = get_customer_features(customer_id)

    # Customer not found
    if customer_df.empty:
        return None

    # -----------------------------------------------------
    # Prepare model input
    # -----------------------------------------------------

    X = customer_df[FEATURE_COLUMNS]

    # -----------------------------------------------------
    # Model prediction
    # -----------------------------------------------------

    probability = model.predict_proba(X)[0, 1]

    prediction = int(
        model.predict(X)[0]
    )

    # -----------------------------------------------------
    # Risk classification
    # -----------------------------------------------------

    if probability >= 0.75:

        risk_level = "HIGH"

    elif probability >= 0.50:

        risk_level = "MEDIUM"

    else:

        risk_level = "LOW"

    # =====================================================
    # SHAP EXPLAINABILITY
    # =====================================================

    # Get the preprocessing step from the saved pipeline
    imputer = model.named_steps["imputer"]

    # Apply EXACT same imputation used during model training
    X_imputed = pd.DataFrame(
        imputer.transform(X),
        columns=X.columns,
        index=X.index
    )

    # -----------------------------------------------------
    # Calculate SHAP values
    # -----------------------------------------------------

    shap_result = shap_explainer(
        X_imputed,
        check_additivity=False
    )

    shap_values = shap_result.values[0]

    # -----------------------------------------------------
    # Create explanation dataframe
    # -----------------------------------------------------

    explanation = pd.DataFrame({
        "feature": X.columns,

        # ACTUAL customer value
        "feature_value": X.iloc[0].values,

        # VALUE actually passed to XGBoost
        # after median imputation
        "model_value": X_imputed.iloc[0].values,

        # SHAP contribution
        "shap_value": shap_values
    })

    # =====================================================
    # TOP CHURN DRIVERS
    # =====================================================

    churn_drivers = (
        explanation[
            explanation["shap_value"] > 0
        ]
        .sort_values(
            "shap_value",
            ascending=False
        )
        .head(3)
        .reset_index(drop=True)
    )

    # =====================================================
    # PROTECTIVE FACTORS
    # =====================================================

    protective_factors = (
        explanation[
            explanation["shap_value"] < 0
        ]
        .sort_values(
            "shap_value",
            ascending=True
        )
        .head(3)
        .reset_index(drop=True)
    )

    # =====================================================
    # BUSINESS RECOMMENDATION
    # =====================================================

    if risk_level == "HIGH":

        recommendation = (
            "Prioritize this customer for a retention "
            "or reactivation campaign."
        )

    elif risk_level == "MEDIUM":

        recommendation = (
            "Monitor this customer and consider a "
            "targeted engagement campaign."
        )

    else:

        recommendation = (
            "Continue regular engagement; no immediate "
            "retention intervention is required."
        )

    # =====================================================
    # RETURN RESULTS
    # =====================================================

    return {
        "customer_id": int(customer_id),

        "churn_probability": float(
            probability
        ),

        "prediction": prediction,

        "risk_level": risk_level,

        "churn_drivers": churn_drivers,

        "protective_factors": protective_factors,

        "explanation": explanation,

        "recommendation": recommendation,
    }

# =========================================================
# GET CUSTOMER PURCHASE HISTORY
# =========================================================

def get_purchase_history(customer_id, limit=20):
    """
    Retrieve recent purchase history for one customer.
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

    df = pd.read_sql(
        query,
        engine,
        params={
            "customer_id": customer_id,
            "limit": limit
        }
    )

    return df

# =========================================================
# GET CUSTOMER PURCHASE TREND
# =========================================================

def get_customer_purchase_trend(customer_id):
    """
    Get monthly purchase activity for one customer.
    """

    query = """
    SELECT
        DATE_FORMAT(invoice_date, '%%Y-%%m-01') AS month,
        COUNT(DISTINCT invoice) AS orders,
        SUM(quantity) AS quantity,
        SUM(revenue) AS revenue
    FROM transactions
    WHERE customer_id = %(customer_id)s
    GROUP BY DATE_FORMAT(invoice_date, '%%Y-%%m-01')
    ORDER BY month
    """

    df = pd.read_sql(
        query,
        engine,
        params={
            "customer_id": customer_id
        }
    )

    if not df.empty:
        df["month"] = pd.to_datetime(df["month"])

    return df