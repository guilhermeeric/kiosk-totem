# totem-checkout — backend

FastAPI + uvicorn hello-world checkout service.

## Layout

```
backend/
  pyproject.toml      # deps + pyproject (uv)
  src/
    main.py            # app root: bootstraps uvicorn  (run this)
    http/              # HTTP layer: FastAPI routes/app
      app.py
    usecases/          # business logic (TODO)
    domain/            # domain models/entities (TODO)
    infrastructure/    # DB, external adapters (TODO)
    tests/             # pytest tests (TODO)
```

## Run (dev)

```bash
cd backend
uv sync                 # first time: create .venv + install deps
uv run python -m src.main                    # no reload
APP_RELOAD=true uv run python -m src.main    # auto-reload on save
```

Server listens on `http://0.0.0.0:8000`.

## Endpoints

- `GET /`       -> `{"message": "Hello, world!"}`
- `GET /health` -> `{"status": "ok"}`

## Config via env vars

| Var         | Default  | Purpose         |
|-------------|----------|-----------------|
| `APP_HOST`  | `0.0.0.0` | Bind address    |
| `APP_PORT`  | `8000`    | Listen port     |
| `APP_RELOAD`| `false`   | Dev auto-reload |