from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Chemin vers la bibliothèque Calibre (monté en volume Docker)
    calibre_library_path: Path = Path("/calibre-library")

    # Nombre de livres par page
    items_per_page: int = 20

    # Niveau de log
    log_level: str = "info"

    # Authentification in-app
    app_password: str = ""          # Obligatoire — APP_PASSWORD dans .env
    session_secret: str = "change-me-in-production"  # SESSION_SECRET dans .env

    @property
    def calibre_db_path(self) -> Path:
        return self.calibre_library_path / "metadata.db"


settings = Settings()
