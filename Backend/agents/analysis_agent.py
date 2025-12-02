# agents/analysis_agent.py
from llm import stream_llm_analysis, stream_llm_analysis_fallback
import pandas as pd
import numpy as np

def analyze_data_stream(df: pd.DataFrame, user_query: str):
    
    # just for cleaning, dont fucking change the dataframe

    if df.empty:
        yield "⚠️ No data returned for this query."
        return

    try:
        
        total_rows = len(df)
    
        #this info is passed to frontend modified ab agay isko theek krna hay to parse and add line breaks
        stats_summary = {}
        numeric_cols = df.select_dtypes(include=['number', 'int64', 'float64']).columns
        
        for col in numeric_cols:
            try:
                
                clean_col = df[col].dropna()
                
                if len(clean_col) > 0:
                    stats_summary[col] = {
                        'count': len(clean_col),
                        'mean': float(clean_col.mean()),
                        'min': float(clean_col.min()),
                        'max': float(clean_col.max()),
                        'sum': float(clean_col.sum()),
                        'median': float(clean_col.median())
                    }
            except Exception as col_error:
                print(f"⚠️ Skipping column {col}: {col_error}")
                continue
        
        # Get unique counts for text columns
        text_stats = {}
        text_cols = df.select_dtypes(include=['object']).columns
        for col in text_cols[:5]:  # Limit to first 5 text columns this has to be decided how to handle large number of text columns
            try:
                text_stats[col] = {
                    'unique_count': int(df[col].nunique()),
                    'top_value': str(df[col].mode()[0]) if len(df[col].mode()) > 0 else 'N/A'
                }
            except:
                continue
        
        sample_size = min(30, len(df))  # Reduced to 30 for better performance this as well has to be discussed
        data_sample = df.head(sample_size).fillna('NULL').to_dict(orient="records")
        
        
        stats_str = ""
        for col, stats in list(stats_summary.items())[:5]:  # Top 5 numeric columns
            stats_str += f"\n• {col}: Min={stats['min']:,.2f}, Max={stats['max']:,.2f}, Avg={stats['mean']:,.2f}"
        
        text_stats_str = ""
        for col, stats in list(text_stats.items())[:3]:  # Top 3 text columns
            text_stats_str += f"\n• {col}: {stats['unique_count']} unique values"
        
        # Enhanced prompt with clearer instructions
        prompt = f"""Analyze this customs import data and provide a brief, structured analysis.

USER QUESTION: {user_query}

DATA OVERVIEW:
- Total Records: {total_rows:,}
- Columns Available: {len(df.columns)}
- Numeric Columns: {len(numeric_cols)}
- Text Columns: {len(text_cols)}

KEY STATISTICS:{stats_str}

TEXT FIELD SUMMARY:{text_stats_str}

SAMPLE DATA (first {sample_size} rows):
{data_sample}

PROVIDE A STRUCTURED ANALYSIS:

📊 KEY COUNTS
• Total records and important aggregate numbers (2-3 points)

📈 PATTERNS OBSERVED  
• Notable trends or distributions in the data (2-3 points)

⚠️ ANOMALIES OR RED FLAGS
• Any unusual findings or data quality issues (1-2 points)

💡 RECOMMENDATIONS
• Actionable next steps based on findings (1-2 points)

RULES:
- Keep total response under 20 lines
- Use bullet points with • symbol
- Include specific numbers from the data
- Be direct and concise
- Focus on the user's question: "{user_query}"

Start immediately with 📊 KEY COUNTS."""

        token_count = 0
        has_content = False
        
        print("🔄 Starting analysis stream...")
        for token in stream_llm_analysis(prompt):
            if token and token.strip():
                has_content = True
                token_count += 1
                yield token
        
        print(f"✅ Streamed {token_count} tokens")
        
        # If no content was streamed, use fallback
        if not has_content:
            print("⚠️ No content from streaming, using fallback...")
            for token in stream_llm_analysis_fallback(prompt):
                yield token
                
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            yield f"""
📊 KEY COUNTS
• Total Records: {len(df):,}
• Columns: {len(df.columns)}
• Data successfully retrieved

📈 PATTERNS OBSERVED
• Query executed successfully
• {len(df):,} records match your criteria

⚠️ ANOMALIES OR RED FLAGS
• Analysis engine error: {str(e)[:100]}
• Raw data is available for manual review

💡 RECOMMENDATIONS
• Check the data sample above
• Try refining your query for better results
• Contact support if error persists
"""
        except:
            yield "\n\n❌ Critical error in analysis. Please check backend logs."



#below is the old implementation for analysis_agent.py
# # agents/analysis_agent.py
# from llm import stream_llm
# import pandas as pd

# def analyze_data_stream(df: pd.DataFrame, user_query: str):
#     if df.empty:
#         yield "No data returned for this query."
#         return

#     # Limit data size for better performance
#     data_sample = df.head(100).to_dict(orient="records")
    
#     prompt = f"""
# You are a data analysis assistant for customs import data.
# Here is the user question:
# {user_query}

# Here is the returned data (showing first 100 rows if more exist):
# Total rows: {len(df)}
# {data_sample}

# Provide:
# - Summary of findings
# - Patterns and trends
# - Outliers or anomalies
# - Any compliance issues or red flags
# - Useful insights and recommendations
# """

#     # Yield tokens from LLM stream
#     for token in stream_llm(prompt):
#         yield token
