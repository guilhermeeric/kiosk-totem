"""Global exception handlers mapping domain errors to HTTP responses.

One module owns error translation: domain NotFound subclasses become 404,
any other ValueError becomes 400. Registered once on the FastAPI app.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.domain.exceptions import CartNotFound, ItemNotFound, OrderNotFound


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(CartNotFound)
    @app.exception_handler(ItemNotFound)
    @app.exception_handler(OrderNotFound)
    async def not_found_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def bad_request_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
