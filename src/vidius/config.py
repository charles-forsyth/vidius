import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

MODELS = {
    "standard": "veo-3.1-generate-preview",
    "fast": "veo-3.1-fast-generate-preview",
    "lite": "veo-3.1-lite-generate-preview",
}


class Settings(BaseSettings):
    # Auth: Gemini API key (preferred; restrict it to the Generative Language API),
    # otherwise Vertex AI with Application Default Credentials.
    api_key: Optional[str] = None
    project_id: str = "ucr-research-computing"
    location: str = "us-central1"
    model_id: str = MODELS["standard"]

    # Path to history file
    history_file: Path = Path(".history.json")

    # Default output directory
    output_dir: Path = Path(os.path.expanduser("~/Videos/Vidius"))

    model_config = SettingsConfigDict(
        env_file=os.path.expanduser("~/.config/vidius/.env"), env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
