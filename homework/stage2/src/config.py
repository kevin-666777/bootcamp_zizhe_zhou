"""Load project settings from a local .env file."""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


def load_env(env_path: str | Path = DEFAULT_ENV_PATH, *, override: bool = False) -> bool:
    """Load environment variables from ``env_path``.

    Existing shell variables are preserved unless ``override`` is true.
    """
    return load_dotenv(dotenv_path=Path(env_path), override=override)


def get_key(name: str, default: str | None = None) -> str | None:
    """Return an environment variable after ``load_env`` has been called."""
    return os.getenv(name, default)
