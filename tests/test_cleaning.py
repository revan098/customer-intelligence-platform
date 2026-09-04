import pandas as pd


def test_cleaned_sales_file_exists():
    file_path = "data/processed/retail_sales_cleaned.csv"

    df = pd.read_csv(file_path, nrows=5)

    assert not df.empty


def test_customer_transactions_file_exists():
    file_path = "data/processed/customer_transactions.csv"

    df = pd.read_csv(file_path, nrows=5)

    assert not df.empty


def test_cleaned_sales_columns_exist():
    file_path = "data/processed/retail_sales_cleaned.csv"

    df = pd.read_csv(file_path, nrows=5)

    required_columns = {
        "invoice",
        "stock_code",
        "description",
        "quantity",
        "invoice_date",
        "price",
        "customer_id",
        "country",
        "revenue",
    }

    assert required_columns.issubset(df.columns)


def test_customer_transactions_have_customer_ids():
    file_path = "data/processed/customer_transactions.csv"

    df = pd.read_csv(file_path, nrows=1000)

    assert df["customer_id"].notna().all()


def test_customer_transactions_have_positive_quantity():
    file_path = "data/processed/customer_transactions.csv"

    df = pd.read_csv(file_path, nrows=1000)

    assert (df["quantity"] > 0).all()


def test_customer_transactions_have_valid_prices():
    file_path = "data/processed/customer_transactions.csv"

    df = pd.read_csv(file_path, nrows=1000)

    assert (df["price"] > 0).all()


def test_customer_transactions_have_valid_revenue():
    file_path = "data/processed/customer_transactions.csv"

    df = pd.read_csv(file_path, nrows=1000)

    calculated_revenue = df["quantity"] * df["price"]

    assert (
        (df["revenue"] - calculated_revenue).abs() < 0.01
    ).all()