from pydantic import BaseModel
from typing import Optional, List, Dict

class DocumentResponse(BaseModel):
    success: bool
    filename: str
    message: str
    word_count: Optional[int] = None

class DocumentChunksResponse(BaseModel):
    success: bool
    filename: str
    message: str
    total_chunks: int
    total_words: int
    chunks: List[Dict]

class HistoryMessage(BaseModel):
    role: str      # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    filename_filter: Optional[str] = None
    similarity_threshold: float = 0.28
    history: Optional[List[HistoryMessage]] = []   # ← NEW

class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: List[Dict]
    had_context: bool
    model: str