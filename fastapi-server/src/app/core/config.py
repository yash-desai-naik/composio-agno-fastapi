from pydantic_settings import BaseSettings
import os

from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Composio Agno API"
    API_V1_STR: str = "/api/v1"
    COMPOSIO_API_KEY: str
    OPENAI_API_KEY:str
    
    class Config:
        env_file = ".env"

settings = Settings()

# print(f"OPENAI_API_KEY {settings.OPENAI_API_KEY}")