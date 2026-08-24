"""Composition root: builds the app and runs the uvicorn server.

Run from the backend/ directory as:
    uv run python -m src.main
(or from the repo root: uv run --directory backend python -m src.main).
"""

import os

import uvicorn

HOST = os.getenv("APP_HOST", "0.0.0.0")
PORT = int(os.getenv("APP_PORT", "8000"))
RELOAD = os.getenv("APP_RELOAD", "false").lower() in {"1", "true", "yes"}


def run() -> None:
    uvicorn.run(
        "src.http.app:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
    )


if __name__ == "__main__":
    run()
