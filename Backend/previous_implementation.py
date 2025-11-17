from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import requests
import json
from io import BytesIO

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


uploaded_data = {}

REQUIRED_COLUMNS = [
    'GD_NO_Complete', 'NTN', 'IMPORTER NAME', 'HS CODE', 'ITEM DESCRIPTION',
    'Declared Unit PRICE', 'ORIGIN COUNTRY', 'ASSD QTY', 'ASSD UNIT',
    'ASSD UNIT PRICE', 'ASSD CURR', 'ASSESSED IMPORT VALUE RS',
    'Customs Duty PAID', 'Sales Tax PAID', 'Income Tax PAID',
    'Additional Custom Duty PAID', 'ADD SALES TAX PAID', 'REG.DUTY PAID',
    'GST PAID', 'Total', 'SRO'
]

class QueryRequest(BaseModel):
    message: str
    session_id: str = "default_session"

@app.get("/")
async def root():
    return {"message": "Customs Data Analysis API is running"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        

        missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        

        session_id = "user_session_1"
        uploaded_data[session_id] = df
        

        summary = {
            "totalRows": len(df),
            "uniqueImporters": int(df['IMPORTER NAME'].nunique()),
            "uniqueHSCodes": int(df['HS CODE'].nunique()),
            "uniqueCountries": int(df['ORIGIN COUNTRY'].nunique()),
            "totalValue": float(df['ASSESSED IMPORT VALUE RS'].sum()),
            "totalDutyPaid": float(df['Customs Duty PAID'].sum()),
            "totalTaxPaid": float(df['Sales Tax PAID'].sum()),
            "columns": df.columns.tolist()
        }
        
        return {"status": "success", "summary": summary, "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/query")
async def query_data(request: QueryRequest):
    import re

    try:
        user_query = request.message.strip()
        session_id = request.session_id

        if session_id not in uploaded_data:
            raise HTTPException(status_code=404, detail="No data uploaded for this session")

        df = uploaded_data[session_id]
        filter_note = "Full dataset used."
        filtered_df = df.copy()

        # -----------------------------------------------------
        # 1️⃣  Detect query intent and apply filters
        # -----------------------------------------------------
        hs_match = re.search(r'\bHS\s*Code\s*(\d+\.?\d*)', user_query, re.IGNORECASE)
        importer_match = re.search(r'\b(importer|company)\s*[:\-]?\s*([\w\s&]+)', user_query, re.IGNORECASE)
        country_match = re.search(r'\bfrom\s+([A-Za-z\s]+)', user_query, re.IGNORECASE)

        if hs_match:
            hs_code = hs_match.group(1)
            filtered_df = df[df['HS CODE'].astype(str).str.contains(hs_code, case=False, na=False)]
            filter_note = f"Filtered {len(filtered_df)} records for HS Code {hs_code}."
        elif importer_match:
            importer_name = importer_match.group(2).strip()
            filtered_df = df[df['IMPORTER NAME'].str.contains(importer_name, case=False, na=False)]
            filter_note = f"Filtered {len(filtered_df)} records for importer '{importer_name}'."
        elif country_match:
            country_name = country_match.group(1).strip()
            filtered_df = df[df['ORIGIN COUNTRY'].str.contains(country_name, case=False, na=False)]
            filter_note = f"Filtered {len(filtered_df)} records for origin country '{country_name}'."

        if filtered_df.empty:
            return {"response": f"No records found for your query. {filter_note}"}

        # -----------------------------------------------------
        # 2️⃣  Compute numeric summaries locally
        # -----------------------------------------------------
        stats = {
            "total_records": len(filtered_df),
            "total_import_value": float(filtered_df['ASSESSED IMPORT VALUE RS'].sum()),
            "avg_unit_price": float(filtered_df['Declared Unit PRICE'].mean()),
            "total_customs_duty": float(filtered_df['Customs Duty PAID'].sum()),
            "total_sales_tax": float(filtered_df['Sales Tax PAID'].sum()),
            "unique_importers": int(filtered_df['IMPORTER NAME'].nunique()),
            "unique_hs_codes": int(filtered_df['HS CODE'].nunique()),
            "unique_countries": int(filtered_df['ORIGIN COUNTRY'].nunique()),
        }

        top_importers = filtered_df['IMPORTER NAME'].value_counts().head(5).to_dict()
        top_countries = filtered_df['ORIGIN COUNTRY'].value_counts().head(5).to_dict()
        top_hs_codes = filtered_df['HS CODE'].value_counts().head(5).to_dict()

        # -----------------------------------------------------
        # 3️⃣  Provide sample rows for grounding (limited)
        # -----------------------------------------------------
        sample_records = filtered_df.sample(min(10, len(filtered_df))).to_dict(orient='records')

        # -----------------------------------------------------
        # 4️⃣  Build concise, structured context for the LLM
        # -----------------------------------------------------
        context = f"""
You are a customs data analysis expert performing post-import audit analysis.

{filter_note}

Data Summary:
- Total Records: {stats['total_records']:,}
- Total Import Value: Rs {stats['total_import_value']:,.2f}
- Avg Declared Unit Price: Rs {stats['avg_unit_price']:,.2f}
- Customs Duty Paid: Rs {stats['total_customs_duty']:,.2f}
- Sales Tax Paid: Rs {stats['total_sales_tax']:,.2f}
- Unique Importers: {stats['unique_importers']}
- HS Codes in this subset: {stats['unique_hs_codes']}
- Origin Countries: {stats['unique_countries']}

Top Importers:
{json.dumps(top_importers, indent=2)}

Top Origin Countries:
{json.dumps(top_countries, indent=2)}

Top HS Codes (if applicable):
{json.dumps(top_hs_codes, indent=2)}

Sample Records (for pattern understanding):
{json.dumps(sample_records, indent=2)}

User Query:
{user_query}

Now, analyze based on the filtered data.
Focus on:
- anomalies, unusual duty/tax ratios, or outliers
- concentration among importers or countries
- potential misclassifications or compliance risks
- actionable audit insights and next steps
Provide a professional and structured analysis.
"""

        # -----------------------------------------------------
        # 5️⃣  Send to LLM (DeepSeek / Ollama)
        # -----------------------------------------------------
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "deepseek-llm:7b",
                "prompt": context,
                "stream": False
            },
            timeout=300
        )

        if response.status_code == 200:
            result = response.json()
            return {"response": result.get("response", "No response generated")}
        else:
            return {"response": f"LLM returned error: {response.status_code} — {response.text}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "sessions": len(uploaded_data),
        "ollama_available": check_ollama()
    }

def check_ollama():
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    import uvicorn
    print("Starting Customs Data Analysis API...")
    print("Make sure Ollama is running with: ollama serve")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)