import sqlite3
import pandas as pd

def run_query_on_customs_db(sql_query: str):
    """
    Run a SQL query on customs.db and return the data as a pandas DataFrame.
    """
    conn = sqlite3.connect("customs.db")
    try:
        df = pd.read_sql_query(sql_query, conn)
        print("df: ", df)
        return df
    finally:
        conn.close()

# if __name__ == "__main__":
#     query = """
#     SELECT * FROM customs WHERE "HS CODE" = '8513.101'
#     """
#     # query = input("Enter your SQL query: ")
#     df = run_query_on_customs_db(query)

