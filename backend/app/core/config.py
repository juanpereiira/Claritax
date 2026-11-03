from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Claritax"
    app_env: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:5173"
    upload_dir: str = "storage/uploads"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()