from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel
from src.app.db.database import db

class User(BaseModel):
    """User representation with SQLite storage"""
    email: str
    name: str
    entity_id: str
    connected_apps: List[str] = []
    chat_history: List[Dict] = []
    created_at: datetime = datetime.now()

    @classmethod
    def from_db(cls, data: dict) -> 'User':
        if not data:
            return None
        return cls(**data)

    @classmethod
    def get(cls, email: str) -> 'User':
        data = db.get_user(email)
        return cls.from_db(data) if data else None

    def save(self) -> 'User':
        if not db.get_user(self.email):
            db.create_user(self.email, self.name, self.entity_id)
        return self

    def update_apps(self) -> None:
        db.update_user_apps(self.email, self.connected_apps)

    def update_chat_history(self) -> None:
        db.update_chat_history(self.email, self.chat_history)