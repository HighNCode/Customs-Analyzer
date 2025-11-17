# agents/sql_agent.py
from llm import call_llm
from db import engine, get_schema
import pandas as pd
from sqlalchemy import text

def generate_sql(schema, user_query: str):
    schema_text = "\n".join([col["column"] for col in schema])

    prompt = f"""
You are an expert SQLite query generator.

RULES (IMPORTANT):
- Table name is `customs`
- USE COLUMN NAMES EXACTLY AS PROVIDED IN SCHEMA.
- IF A COLUMN HAS SPACES OR SPECIAL CHARACTERS, WRAP IT IN BACKTICKS.
- NEVER modify column names (do NOT replace spaces with `_`).
- Return ONLY SQL. No explanation.

Here is the exact schema:
{schema_text}

User question:
\"\"\"{user_query}\"\"\"

Write a valid SQLite SELECT query.
"""
    return call_llm(prompt)

def sanitize_sql(sql: str) -> str:
    """
    Remove extra backslashes and whitespace from multi-line SQL returned by LLM.
    """
    # Remove any literal backslashes at the end of lines
    lines = [line.rstrip(" \\") for line in sql.splitlines()]
    # Join lines into a single string
    return " ".join(lines)
