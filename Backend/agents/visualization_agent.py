import json
from llm import generate_llm_response
from prompts import prompts

def generate_visualization_code(df, user_query: str, analysis_summary: str = ""):
    """
    Generate matplotlib code for visualizing the data
    """
    system_prompt = prompts.VISUALIZATION_GENERATOR_SYSTEM_PROMPT
    
    # Prepare data context
    data_context = {
        "columns": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "row_count": len(df),
        "sample_data": df.head(5).to_dict(orient="records"),
        "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
        "categorical_columns": df.select_dtypes(include=['object', 'category']).columns.tolist()
    }
    
    # Add statistical info for numeric columns
    if data_context["numeric_columns"]:
        stats = df[data_context["numeric_columns"]].describe().to_dict()
        data_context["statistics"] = stats
    
    context_str = json.dumps(data_context, indent=2)
    system_prompt = system_prompt.replace("{{data_context}}", context_str)
    
    user_prompt = f"""
User Query: {user_query}

Analysis Summary: {analysis_summary}

Generate Python code using matplotlib to create an appropriate visualization for this data.
The code should:
1. Be complete and executable
2. Save the plot to a file named 'visualization.png'
3. Use appropriate chart type (bar, line, pie, scatter, etc.)
4. Include proper labels, title, and legend
5. Handle the data appropriately

Return ONLY the Python code, no explanations.
"""
    
    return generate_llm_response(system_prompt, user_prompt)