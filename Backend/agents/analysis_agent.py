# agents/analysis_agent.py
from llm import stream_llm
import pandas as pd

def analyze_data_stream(df: pd.DataFrame, user_query: str):
    if df.empty:
        yield "No data returned for this query."
        return

    # Limit data size for better performance
    data_sample = df.head(100).to_dict(orient="records")
    
    prompt = f"""
You are a data analysis assistant for customs import data.
Here is the user question:
{user_query}

Here is the returned data (showing first 100 rows if more exist):
Total rows: {len(df)}
{data_sample}

Provide:
- Summary of findings
- Patterns and trends
- Outliers or anomalies
- Any compliance issues or red flags
- Useful insights and recommendations
"""

    # Yield tokens from LLM stream
    for token in stream_llm(prompt):
        yield token
