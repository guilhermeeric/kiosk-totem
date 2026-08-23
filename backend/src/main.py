"""Composition root: builds the app and runs the uvicorn server.

Run from the project root (backend/) as:
    uv run --directory backend python -m src.main
or just:
    uv run --directory backend python src/main.py
"""
import os

import uvicorn

from src.http.app import app  # noqa: F401  (imported so uvicorn string target resolves)

HOST = os.getenv("APP_HOST", "0.0.0.0")
PORT = int(os.getenv("APP_PORT", "8000"))
RELOAD = os.getenv("APP_RELOAD", "false").lower() in {"1", "true", "yes"}


def run() -> None:
    uvicorn.run(
        "src.http.app:app",  # string target so --reload works
        host=HOST,
        port=PORT,
        reload=RELOAD,
    )


if __name__ == "__main__":
    run()