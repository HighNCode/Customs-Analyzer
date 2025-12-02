# agents/sql_agent.py
from llm import generate_llm_response
from db import engine, get_schema
import pandas as pd
from sqlalchemy import text
from prompts import prompts
import json

def generate_sql(schema, user_query: str):

#     prompt = f"""
# You are an expert SQLite query generator.

# RULES (IMPORTANT):
# - Table name is 'customs'
# - USE COLUMN NAMES EXACTLY AS PROVIDED IN SCHEMA.
# - IF A COLUMN HAS SPACES OR SPECIAL CHARACTERS, WRAP IT IN SINGLE QUOTES.
# - NEVER modify column names (do NOT replace spaces with '_').
# - Return ONLY SQL. No explanation.

# Here is the exact schema:
# {schema}

# User question:
# \"\"\"{user_query}\"\"\"

# Write a valid SQLite SELECT query.
# """

    system_prompt = prompts.SQL_GENERATOR_SYSTEM_PROMPT
    schema_str = json.dumps(schema, indent=2)
    system_prompt = system_prompt.replace("{{schema}}", schema_str)

    # return call_llm(system_prompt, user_query)
    return generate_llm_response(system_prompt, user_query)

def sanitize_sql(sql: str) -> str:
    
    # Remove any literal backslashes at the end of lines
    lines = [line.rstrip(" \\") for line in sql.splitlines()]
    # Join lines into a single string
    return " ".join(lines)
