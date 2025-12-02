# agents/analysis_agent.py
from llm import stream_llm_analysis
import pandas as pd
import numpy as np
import re

def analyze_data_stream(df: pd.DataFrame, user_query: str):
    
    if df.empty:
        yield "⚠️ No data returned for this query."
        return

    try:
        
        total_rows = len(df)
    
        # Calculate statistics for numeric columns
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
        for col in text_cols[:5]:
            try:
                text_stats[col] = {
                    'unique_count': int(df[col].nunique()),
                    'top_value': str(df[col].mode()[0]) if len(df[col].mode()) > 0 else 'N/A'
                }
            except:
                continue
        
        # Increased sample size for better analysis
        sample_size = min(100, len(df))
        data_sample = df.head(sample_size).fillna('NULL').to_dict(orient="records")
        
        # Build stats strings
        stats_str = ""
        for col, stats in list(stats_summary.items())[:5]:
            stats_str += f"\n• {col}: Min={stats['min']:,.2f}, Max={stats['max']:,.2f}, Avg={stats['mean']:,.2f}"
        
        text_stats_str = ""
        for col, stats in list(text_stats.items())[:3]:
            text_stats_str += f"\n• {col}: {stats['unique_count']} unique values"
        
        # Enhanced prompt with explicit newline instructions
        prompt = f"""You are an Expert on Post Custom Audit Analysis, You are given the information of Customs Import Stats of Pakistan ports, all the monetary value is dealt in PKR .
                Analyze this customs import data. You MUST use proper newlines between all sections and bullet points.

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

PROVIDE YOUR ANALYSIS IN THIS EXACT FORMAT (with newlines after each line):

📊 KEY COUNTS
• [First count]
• [Second count]
• [Third count]

📈 PATTERNS OBSERVED
• [First pattern]
• [Second pattern]
• [Third pattern]

⚠️ ANOMALIES OR RED FLAGS
• [First anomaly]
• [Second anomaly]

💡 RECOMMENDATIONS
• [First recommendation]
• [Second recommendation]

CRITICAL FORMATTING RULES:
1. Add TWO newlines after each section header (📊, 📈, ⚠️, 💡)
2. Add ONE newline after each bullet point (•)
3. Each section must be separated by a blank line
4. Do NOT run sections together
5. Be concise but informative
6. Focus on: "{user_query}"

Begin now with proper formatting:"""

        token_count = 0
        has_content = False
        buffer = ""
        previous_token = ""
        
        print("🔄 Starting analysis stream...")
        
        for token in stream_llm_analysis(prompt):
            if token and token.strip():
                has_content = True
                token_count += 1
                
                # Smart newline insertion logic
                # If we see an emoji header without newlines before it, add them
                if re.match(r'^[📊📈💡⚠️🔍]', token) and previous_token and not previous_token.endswith('\n'):
                    yield '\n\n'  # Add spacing before new section
                
                # If current token is a bullet and previous wasn't a newline, add one
                if token.startswith('•') and previous_token and not previous_token.endswith('\n'):
                    yield '\n'
                
                yield token
                previous_token = token
        
        print(f"✅ Streamed {token_count} tokens")
        
        # If no content was streamed, use fallback
        # if not has_content:
        #     print("⚠️ No content from streaming, using fallback...")
        #     for token in stream_llm_analysis_fallback(prompt):
        #         yield token
                
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