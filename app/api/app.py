from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.exceptions import ApplicationError
from app.core.logging_config import (
    configure_logging,
    create_request_id,
    get_request_id,
)

configure_logging()

app = FastAPI(
    title="AI-Enabled RAG Knowledge Assistant",
    version="0.3.0",
    description=(
        "Grounded technical-support retrieval and generation API over "
        "synthetic incident, runbook and FAQ knowledge."
    ),
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    create_request_id()
    response = await call_next(request)
    response.headers["X-Request-ID"] = get_request_id()
    return response


@app.exception_handler(ApplicationError)
async def application_error_handler(
    request: Request,
    exc: ApplicationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "request_id": get_request_id(),
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )


app.include_router(router)
