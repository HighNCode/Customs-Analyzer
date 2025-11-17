# db.py
import pandas as pd
from sqlalchemy import create_engine, text

DATABASE_URL = "sqlite:///customs.db"
engine = create_engine(DATABASE_URL)

def load_csv_to_db(csv_path: str):
    df = pd.read_csv(csv_path)
    df.to_sql("customs", engine, if_exists="replace", index=False)

def load_xlsx_to_db(xlsx_path: str, sheet_name=0):
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
    df.to_sql("customs", engine, if_exists="replace", index=False)

def get_schema():
    schema_query = "PRAGMA table_info(customs)"
    with engine.connect() as conn:
        rows = conn.execute(text(schema_query)).fetchall()

    schema = [{"column": r[1], "type": r[2]} for r in rows]
    return schema
