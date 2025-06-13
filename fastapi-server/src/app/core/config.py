from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Composio Agno API"
    API_V1_STR: str = "/api/v1"
    COMPOSIO_API_KEY: str
    
    class Config:
        env_file = ".env"

settings = Settings()