FROM python:3.12-slim

WORKDIR /app

RUN pip install uv --no-cache-dir

COPY pyproject.toml ./

RUN uv sync

COPY src/ ./src/

EXPOSE 8000

CMD ["uv", "run", "python", "-m", "src.main"]
