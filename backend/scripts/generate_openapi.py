"""Regenerate the committed OpenAPI spec at the repo root.

Run from backend/:
    uv run python scripts/generate_openapi.py

The spec is a snapshot of the live /openapi.json; regenerate it whenever
the HTTP surface changes (endpoints, schemas, tags, summaries).
"""

import json
from pathlib import Path

from src.http.app import app

OUT_PATH = Path(__file__).resolve().parents[2] / "openapi.json"


def main() -> None:
    spec = app.openapi()
    OUT_PATH.write_text(json.dumps(spec, indent=2, default=str) + "\n")
    print(f"OpenAPI spec written to {OUT_PATH}")


if __name__ == "__main__":
    main()
