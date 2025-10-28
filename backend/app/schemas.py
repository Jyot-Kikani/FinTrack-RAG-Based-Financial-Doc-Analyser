# app/schemas.py
from pydantic import BaseModel
from typing import List, Dict, Any

class ChatRequest(BaseModel):
    question: str
    chat_history: List[Dict[str, Any]] = []

class UploadResponse(BaseModel):
    message: str
    file_name: str

class ChatResponse(BaseModel):
    answer: str