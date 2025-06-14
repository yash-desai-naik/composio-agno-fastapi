from pydantic import BaseModel, EmailStr
from typing import List, Dict
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    pass

class UserResponse(BaseModel):
    email: str
    name: str
    entity_id: str
    connected_apps: List[str]
    chat_history: List[Dict]
    created_at: datetime

class ConnectionRequest(BaseModel):
    app_name: str

class ToolCall(BaseModel):
    agent: str | None
    tool: str | None
    input: dict | None
    output: dict | None

class ChatRequest(BaseModel):
    query: str
    timezone: str = "Asia/Kolkata"

class ChatResponse(BaseModel):
    query: str
    response: str
    tool_calls: List[ToolCall] = []

class AvailableApps(BaseModel):
    oauth_apps: List[str]
    no_auth_apps: List[str]