from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv(
    "MYSQL_DATABASE",
    "customer_intelligence"
)

connection_string = (
    f"mysql+pymysql://{MYSQL_USER}:"
    f"{MYSQL_PASSWORD}@{MYSQL_HOST}:"
    f"{MYSQL_PORT}/{MYSQL_DATABASE}"
)

engine = create_engine(connection_string)