"""Environment and path configuration helpers for the project."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


def load_env(env_path: str | Path = DEFAULT_ENV_PATH, *, override: bool = False) -> bool:
    """Load environment variables from a project-local dotenv file.

    Args:
        env_path: Path to the dotenv file. Relative paths are resolved from
            the project root.
        override: Whether dotenv values should replace existing variables.

    Returns:
        True when a dotenv file was found and loaded, otherwise False.
    """
    path = Path(env_path).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return load_dotenv(dotenv_path=path, override=override)


def get_key(name: str, default: str | None = None, *, required: bool = False) -> str | None:
    """Return an environment variable without exposing it in logs.

    Args:
        name: Environment variable name.
        default: Value returned when the variable is not set.
        required: Raise a clear error if the value is missing or empty.
    """
    if not name or not name.strip():
        raise ValueError("Environment variable name must be non-empty.")

    value = os.getenv(name, default)
    if required and (value is None or value == ""):
        raise RuntimeError(
            f"Required environment variable {name!r} is missing. "
            "Copy .env.example to .env and provide a local value."
        )
    return value


def get_path(name: str, default: str, *, create: bool = False) -> Path:
    """Resolve an environment-driven path relative to the project root.

    Args:
        name: Environment variable containing the path.
        default: Fallback path when the variable is not set.
        create: Create the resolved directory when it does not exist.
    """
    configured = get_key(name, default)
    if configured is None or configured == "":
        raise ValueError(f"No path configured for {name!r}.")

    path = Path(configured).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path = path.resolve()
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path
