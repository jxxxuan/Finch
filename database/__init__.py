from sqlalchemy import create_engine
from psycopg2 import pool
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

USERNAME = os.getenv("DB_USERNAME")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("HOST")
PRODUCTION = os.getenv("PRODUCTION", "False").lower() == "true"

def create_conn():
    return psycopg2.connect(
        dbname="predictor",
        user=USERNAME,
        password=PASSWORD,
        host=HOST,
        port=5432
    )

def create_pandas_conn():
    engine = create_engine(
        f"postgresql+psycopg2://{USERNAME}:{PASSWORD}@{HOST}:5432/predictor"
    )
    return engine.connect()

def create_db_pool(max_conn):
    return pool.SimpleConnectionPool(
        1,  # 最少连接数
        max_conn, # 最大连接数
        dbname="predictor",
        user=USERNAME,
        password=PASSWORD,
        host=HOST,
        port=5432
    )