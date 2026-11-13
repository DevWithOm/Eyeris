from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    app_name: str = "retina-screening"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://retina_user:change_me@localhost:5432/retina_screening"
    storage_root: str = "./storage"
    max_upload_mb: int = 15
    cors_origins: list[str] = ["http://localhost:5173"]
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
settings = Settings()
