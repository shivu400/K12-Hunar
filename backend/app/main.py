import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import close_db_pool, init_db_pool
from app.routers import auth, inquiries


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager: initializes database connection pool
    on server startup and tears it down gracefully on shutdown.
    """
    init_db_pool()
    yield
    close_db_pool()


app = FastAPI(
    title="EdTech Inquiry and CRM API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

settings = get_settings()

# CORS Middleware: Restrict credentialed cross-origin requests to explicitly allowed frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
)


# Consistent JSON validation error response formatter
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = {}
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err["loc"] if loc not in ("body", "query"))
        errors[field or "non_field_error"] = err["msg"]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error. Please verify the submitted data.",
            "errors": errors,
        },
    )


# Health check endpoint
@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "connected",
    }


# Include Routers
app.include_router(auth.router)
app.include_router(inquiries.router)

# Production SPA Static File Serving
# If the frontend has been built into frontend/dist, serve it seamlessly
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")

# Also check fallback if run from within backend directory
if not os.path.exists(STATIC_DIR):
    ALT_STATIC_DIR = os.path.join(os.getcwd(), "..", "frontend", "dist")
    if os.path.exists(ALT_STATIC_DIR):
        STATIC_DIR = ALT_STATIC_DIR
    else:
        ALT_STATIC_DIR_2 = os.path.join(os.getcwd(), "frontend", "dist")
        if os.path.exists(ALT_STATIC_DIR_2):
            STATIC_DIR = ALT_STATIC_DIR_2

if os.path.exists(STATIC_DIR):
    # Mount assets folder
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # SPA Fallback for non-API routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api"):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "API endpoint not found."},
            )
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
