from pathlib import Path
from datetime import datetime

import joblib
import pandas as pd

from src.database import engine


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "churn_xgb_pipeline.joblib"
)


# ============================================================
# MODEL FEATURES
# ============================================================

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


# ============================================================
# LOAD CUSTOMER FEATURES
# ============================================================

def load_customer_features():

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
    FROM customer_churn_modeling
    """

    df = pd.read_sql(
        query,
        engine
    )

    return df


# ============================================================
# LOAD MODEL
# ============================================================

def load_model():

    if not MODEL_PATH.exists():

        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}"
        )

    model = joblib.load(
        MODEL_PATH
    )

    return model


# ============================================================
# GENERATE PREDICTIONS
# ============================================================

def generate_predictions():

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    customers = (
        load_customer_features()
    )

    if customers.empty:

        raise ValueError(
            "No customer features found."
        )

    # --------------------------------------------------------
    # LOAD MODEL
    # --------------------------------------------------------

    model = load_model()

    # --------------------------------------------------------
    # PREPARE FEATURES
    # --------------------------------------------------------

    X = customers[
        FEATURE_COLUMNS
    ]

    # --------------------------------------------------------
    # PREDICT PROBABILITY
    # --------------------------------------------------------

    customers[
        "churn_probability"
    ] = model.predict_proba(
        X
    )[:, 1]

    # --------------------------------------------------------
    # PREDICT CLASS
    # --------------------------------------------------------

    customers[
        "prediction"
    ] = model.predict(
        X
    )

    # --------------------------------------------------------
    # RISK LEVEL
    # --------------------------------------------------------

    customers[
        "risk_level"
    ] = pd.cut(
        customers[
            "churn_probability"
        ],

        bins=[
            -float("inf"),
            0.50,
            0.75,
            float("inf"),
        ],

        labels=[
            "LOW",
            "MEDIUM",
            "HIGH",
        ],

        right=False,
    )

    customers[
        "risk_level"
    ] = customers[
        "risk_level"
    ].astype(str)

    # --------------------------------------------------------
    # PREDICTION DATE
    # --------------------------------------------------------

    prediction_date = datetime.now()

    customers[
        "prediction_date"
    ] = prediction_date

    # --------------------------------------------------------
    # SELECT OUTPUT
    # --------------------------------------------------------

    predictions = customers[
        [
            "customer_id",
            "churn_probability",
            "prediction",
            "risk_level",
            "prediction_date",
        ]
    ].copy()

    return predictions


# ============================================================
# SAVE PREDICTIONS TO MYSQL
# ============================================================

def save_predictions(predictions):

    if predictions.empty:

        raise ValueError(
            "No predictions to save."
        )

    connection = engine.raw_connection()

    try:

        cursor = connection.cursor()

        # ----------------------------------------------------
        # UPSERT
        # ----------------------------------------------------

        query = """
        INSERT INTO churn_predictions (
            customer_id,
            churn_probability,
            prediction,
            risk_level,
            prediction_date
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s
        )
        ON DUPLICATE KEY UPDATE

            churn_probability =
                VALUES(churn_probability),

            prediction =
                VALUES(prediction),

            risk_level =
                VALUES(risk_level),

            prediction_date =
                VALUES(prediction_date)
        """

        records = [
            (
                int(row["customer_id"]),
                float(
                    row["churn_probability"]
                ),
                int(
                    row["prediction"]
                ),
                str(
                    row["risk_level"]
                ),
                row["prediction_date"],
            )
            for _, row in predictions.iterrows()
        ]

        cursor.executemany(
            query,
            records
        )

        connection.commit()

        print(
            f"Saved {len(records):,} predictions."
        )

    except Exception:

        connection.rollback()

        raise

    finally:

        cursor.close()
        connection.close()


# ============================================================
# COMPLETE PIPELINE
# ============================================================

def run_prediction_pipeline():

    print(
        "Starting churn prediction pipeline..."
    )

    predictions = (
        generate_predictions()
    )

    print(
        f"Generated {len(predictions):,} predictions."
    )

    print()
    print(
        "Risk distribution:"
    )

    print(
        predictions[
            "risk_level"
        ]
        .value_counts()
        .sort_index()
    )

    save_predictions(
        predictions
    )

    print()
    print(
        "Prediction pipeline completed successfully."
    )


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_prediction_pipeline()