from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    index_path: Path = Path("data/index.npz")
    model_path: Path = Path("models/all-MiniLM-L6-v2")
    embeddings_path: Path = Path("data/embeddings")
    route_style: Literal["sync", "async"] = "sync"
    backend: Literal["python", "numpy"] = "numpy"
