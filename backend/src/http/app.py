"""HTTP layer: owns the FastAPI application instance and routes."""
from fastapi import FastAPI

app = FastAPI(
    title="totem-checkout backend",
    description="Checkout backend for totem-checkout.",
    version="0.1.0",
)


@app.get("/")
def root() -> dict:
    """Hello-world root endpoint."""
    return {"message": "Hello, world!"}


@app.get("/health")
def health() -> dict:
    """Simple health check."""
    return {"status": "ok"}