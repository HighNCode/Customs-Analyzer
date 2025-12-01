# main.py
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from models.request_models import QueryRequest
from db import engine, get_schema, attach_schema_descriptions
from agents.sql_agent import generate_sql, sanitize_sql
from agents.analysis_agent import analyze_data_stream
import pandas as pd
from sqlalchemy import text
from fastapi.responses import StreamingResponse
from llm import check_ollama
from io import BytesIO
import json
from sql_test import run_query_on_customs_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        "ollama_available": check_ollama()
    }

@app.post("/query")
def run_query_stream(req: QueryRequest):
    user_query = req.question.strip()
    session_id = req.session_id
    schema = get_schema()
    schema = attach_schema_descriptions(schema)
    sql = generate_sql(schema, user_query).strip()
    print(sql)

    import pdb; pdb.set_trace()
    sql = sanitize_sql(sql)

    run_query_on_customs_db(sql)

    return {"status": "success", "sql": sql}

    # try:
    #     df = pd.read_sql(text(sql), engine)
    # except Exception as e:
    #     raise HTTPException(500, f"SQL Error: {e}")

    # df = df.where(pd.notnull(df), None)  # JSON-safe

    # def event_generator():
    #     # First yield metadata
    #     # yield f"data: SQL: {sql}\n\n"
    #     # yield f"data: Rows: {len(df)}\n\n"
        
    #     # Now stream analysis from LLM
    #     for token in analyze_data_stream(df, user_query):
    #         # Just yield the token as-is, don't escape anything
    #         yield f"data: {token}\n\n"

    #     yield "data: [DONE]\n\n"

    # return StreamingResponse(event_generator(), media_type="text/event-stream")
