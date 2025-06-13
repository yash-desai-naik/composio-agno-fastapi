from fastapi import APIRouter, HTTPException
from typing import List
from src.app.schemas.composio import (
    UserCreate,
    UserResponse,
    ConnectionRequest,
    ChatRequest,
    ChatResponse,
    ToolCall
)
from src.app.services.composio import ComposioService

router = APIRouter()
service = ComposioService()

@router.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate):
    return await service.create_user(email=user.email, name=user.name)

@router.get("/users/{email}", response_model=UserResponse)
async def get_user(email: str):
    user = await service.get_user(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/users/{email}/connect")
async def connect_app(email: str, connection: ConnectionRequest):
    try:
        result = await service.connect_app(email, connection.app_name)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{email}/apps", response_model=List[str])
async def get_connected_apps(email: str):
    try:
        return await service.get_connected_apps(email)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/users/{email}/chat", response_model=ChatResponse)
async def process_query(email: str, chat_request: ChatRequest):
    try:
        return await service.process_query(
            email=email,
            query=chat_request.query,
            timezone=chat_request.timezone
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))