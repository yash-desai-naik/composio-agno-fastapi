from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel

class User(BaseModel):
    """User representation with in-memory storage"""
    email: str
    name: str
    entity_id: str
    connected_apps: List[str] = []
    chat_history: List[Dict] = []
    created_at: datetime = datetime.now()