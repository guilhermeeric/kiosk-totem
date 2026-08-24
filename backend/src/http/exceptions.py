"""Global exception handlers mapping domain errors to HTTP responses.

One module owns error translation: domain NotFound subclasses become 404,
any other ValueError becomes 400. Registered once on the FastAPI app.

Handler registration order matters: Starlette matches handlers by insertion
order, so the specific NotFound handler must stay ahead of the generic
ValueError one (a NotFound is also a ValueError).
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.domain.exceptions import NotFound


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFound)
    async def not_found_handler(request: Request, exc: NotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def bad_request_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
