from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, читаются из переменных окружения / .env"""

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    database_url: str = "sqlite:///./data/app.db"
    signals_storage_path: str = "./data/signals"
    images_storage_path: str = "./data/images"
    app_env: str = "development"


settings = Settings()
