import pandas as pd
from pathlib import Path

from database import engine


RAW_FILE = Path(
    "../data/raw/online_retail_II.xlsx"
)

PROCESSED_FILE = Path(
    "../data/processed/retail_sales_cleaned.csv"
)


def load_clean_data():
    df = pd.read_csv(PROCESSED_FILE)

    print(f"Loaded {len(df):,} rows")

    return df

def load_to_mysql(df, table_name="transactions"):
    chunk_size = 10000

    for start in range(0, len(df), chunk_size):

        chunk = df.iloc[
            start:start + chunk_size
        ]

        chunk.to_sql(
            table_name,
            con=engine,
            if_exists="append",
            index=False,
            method="multi"
        )

        print(
            f"Loaded {min(start + chunk_size, len(df)):,}"
            f" / {len(df):,}"
        )
def prepare_for_mysql(df):

    columns = [
        "invoice",
        "stockcode",
        "description",
        "quantity",
        "invoicedate",
        "price",
        "customer_id",
        "country",
        "revenue",
        "is_cancellation",
        "is_return"
    ]

    df = df[columns].copy()

    df = df.rename(columns={
        "stockcode": "stock_code",
        "invoicedate": "invoice_date"
    })

    return df

if __name__ == "__main__":

    df = load_clean_data()

    df = prepare_for_mysql(df)

    load_to_mysql(df)

    print("ETL completed successfully.")