"""Loads the repo-root .env into process environment, for local development
only. In any real deployment the platform (Railway/Render/etc) injects
environment variables directly — this exists only so `uv run uvicorn
app.main:app` picks up the same single .env every other part of this repo
already reads (see .env.example). Real environment variables always win: a
key already set in the process environment is never overwritten by a
stray .env file, so this is inert in production.
"""

from __future__ import annotations

import os
from pathlib import Path

_ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".env"


def load_repo_root_env() -> None:
    if not _ENV_PATH.exists():
        return
    for raw_line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")
