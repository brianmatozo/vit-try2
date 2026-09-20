from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "backend server"
    database_url: str = "sqlite:///./server/data/test.db"
    secret_key: str = "vitalcer-dev-secret-key"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
