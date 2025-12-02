# main.py
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from models.request_models import QueryRequest
from db import engine, get_schema, attach_schema_descriptions
from agents.sql_agent import generate_sql, sanitize_sql
from agents.analysis_agent import analyze_data_stream
import pandas as pd
from sqlalchemy import text
from fastapi.responses import StreamingResponse, Response
from io import BytesIO
import json
import hashlib
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store query results temporarily (in production use Redis or similar)
query_results_cache = {}

@app.get("/")
async def root():
    return {"message": "Customs Data Analysis API is running"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        df.to_sql("customs", engine, if_exists="replace", index=False)
        
        summary = {
            "totalRows": len(df),
            "uniqueImporters": int(df['IMPORTER NAME'].nunique()) if 'IMPORTER NAME' in df.columns else 0,
            "uniqueHSCodes": int(df['HS CODE'].nunique()) if 'HS CODE' in df.columns else 0,
            "uniqueCountries": int(df['ORIGIN COUNTRY'].nunique()) if 'ORIGIN COUNTRY' in df.columns else 0,
            "totalValue": float(df['ASSESSED IMPORT VALUE RS'].sum()) if 'ASSESSED IMPORT VALUE RS' in df.columns else 0,
            "totalDutyPaid": float(df['Customs Duty PAID'].sum()) if 'Customs Duty PAID' in df.columns else 0,
            "totalTaxPaid": float(df['Sales Tax PAID'].sum()) if 'Sales Tax PAID' in df.columns else 0,
            "columns": df.columns.tolist()
        }

        session_id = "user_session_1"
        
        return {"status": "success", "summary": summary, "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health_check():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM customs"))
            row_count = result.scalar()
    except:
        row_count = 0
    
    return {
        "status": "healthy",
        "rows_in_database": row_count,
    }

def detect_data_request(query: str) -> bool:
    """Detect if user is asking for specific data rather than just analysis"""
    data_keywords = [
        'gd number', 'gd_no', 'list', 'show me', 'give me',
        'importer name', 'ntn', 'hs code', 'specific', 'which',
        'audit prone', 'suspicious', 'flagged', 'cases'
    ]
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in data_keywords)

@app.post("/query")
def run_query_stream(req: QueryRequest):
    """
    Main query endpoint with data export capability
    """
    user_query = req.question.strip()
    session_id = req.session_id
    
    print(f"\n{'='*60}")
    print(f"🔥 NEW QUERY: {user_query}")
    print(f"🆔 Session: {session_id}")
    print(f"{'='*60}\n")
    
    # Get schema with descriptions
    schema = get_schema()
    schema = attach_schema_descriptions(schema)
    
    # Generate SQL
    print("🔄 Generating SQL...")
    sql = generate_sql(schema, user_query).strip()
    print(f"✅ Generated SQL:\n{sql}\n")
    
    # Sanitize SQL
    sql = sanitize_sql(sql)
    
    # Execute SQL query
    try:
        print("🔄 Executing SQL query...")
        df = pd.read_sql(text(sql), engine)
        print(f"✅ Query returned {len(df)} rows")
        print(f"📋 Columns: {df.columns.tolist()}\n")
    except Exception as e:
        error_msg = f"SQL Execution Error: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(500, error_msg)

    # Store result in cache for download
    result_id = hashlib.md5(f"{user_query}{datetime.now().isoformat()}".encode()).hexdigest()
    query_results_cache[result_id] = df.copy()
    
    # Detect if user wants specific data
    wants_data = detect_data_request(user_query)
    
    # Handle NULL values for JSON serialization
    df = df.where(pd.notnull(df), None)

    # Stream analysis
    def event_generator():
        # Send metadata with result_id and data preview
        metadata = {
            "type": "metadata", 
            "sql": sql.replace('"', "'"), 
            "rows": len(df),
            "result_id": result_id,
            "wants_data": wants_data,
            "columns": df.columns.tolist()
        }
        
        # If small dataset and user wants data, include preview
        if wants_data and len(df) <= 50:
            preview_df = df.head(50).copy()
            metadata["data_preview"] = preview_df.to_dict(orient="records")
        
        yield f"data: {json.dumps(metadata)}\n\n"
        print(f"📤 Sent metadata: {len(df)} rows\n")
        
        # Stream analysis tokens
        print("🔄 Starting analysis stream...\n")
        token_count = 0
        
        try:
            for token in analyze_data_stream(df, user_query):
                if token:
                    token_count += 1
                    
                    token_json = json.dumps({
                        "type": "token",
                        "content": token
                    })
                    
                    yield f"data: {token_json}\n\n"
                    
                    if token_count % 20 == 0:
                        print(f"📤 Streamed {token_count} tokens...")
            
            print(f"\n✅ Analysis complete - Total tokens: {token_count}")
            
        except Exception as e:
            print(f"❌ Streaming error: {e}")
            error_json = json.dumps({
                "type": "token",
                "content": f"\n\n⚠️ Error: {str(e)}"
            })
            yield f"data: {error_json}\n\n"
        
        done_json = json.dumps({"type": "done"})
        yield f"data: {done_json}\n\n"
        print(f"{'='*60}\n")

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/download/{result_id}")
async def download_result(result_id: str, format: str = "excel"):
    

    if result_id not in query_results_cache:
        raise HTTPException(404, "Result not found or expired")
    
    df = query_results_cache[result_id]
    
    if format == "excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Query Results')
        output.seek(0)
        
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=customs_query_{result_id[:8]}.xlsx"
            }
        )
    
    elif format == "csv":
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=customs_query_{result_id[:8]}.csv"
            }
        )
    
    elif format == "json":
        return Response(
            content=df.to_json(orient="records", indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=customs_query_{result_id[:8]}.json"
            }
        )
    
    else:
        raise HTTPException(400, "Invalid format. Use 'excel', 'csv', or 'json'")