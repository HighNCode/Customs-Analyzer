# models/request_models.py
from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str
    session_id: str