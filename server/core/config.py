import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "backend server"
    database_url: str = "sqlite:///./server/data/test.db"
    secret_key: str = "vitalcer-dev-secret-key"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def ensure_sqlite_dir(self) -> None:
        if "sqlite" in self.database_url:
            raw_path = self.database_url.split("///")[-1]
            if raw_path and not raw_path.startswith(":memory:"):
                db_dir = Path(raw_path).parent
                if db_dir and str(db_dir) != ".":
                    os.makedirs(db_dir, exist_ok=True)


settings = Settings()
settings.ensure_sqlite_dir()
