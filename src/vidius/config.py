import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_id: str = "ucr-research-computing"
    location: str = "us-central1"
    model_id: str = "veo-3.0-generate-preview"

    # Path to history file
    history_file: Path = Path(".history.json")

    # Default output directory
    output_dir: Path = Path(os.path.expanduser("~/Videos/Vidius"))

    model_config = SettingsConfigDict(
        env_file=os.path.expanduser("~/.config/vidius/.env"), env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
