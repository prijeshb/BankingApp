from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base
from app.common.logging import configure_logging
from app.common.middleware import CorrelationIDMiddleware
from app.common.exceptions import (
    BankingException,
    banking_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from app.common.health import router as health_router
from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.accounts.router import router as accounts_router
from app.transactions.router import router as transactions_router
from app.transfers.router import router as transfers_router
from app.cards.router import router as cards_router
from app.statements.router import router as statements_router

# Import all models so SQLAlchemy/Alembic discovers them
import app.users.models  # noqa: F401
import app.auth.models  # noqa: F401
import app.accounts.models  # noqa: F401
import app.transactions.models  # noqa: F401
import app.cards.models  # noqa: F401
import app.audit.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(debug=settings.DEBUG)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# --- Middleware (outermost first) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationIDMiddleware)

# --- Exception handlers ---
app.add_exception_handler(BankingException, banking_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# --- Routers ---
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(accounts_router)
app.include_router(transactions_router)
app.include_router(transfers_router)
app.include_router(cards_router)
app.include_router(statements_router)

# --- Static frontend (only present in Docker / after `npm run build`) ---
_static = Path(__file__).parent.parent / "static"
if _static.exists():
    # Serve hashed JS/CSS/image assets built by Vite
    app.mount("/assets", StaticFiles(directory=str(_static / "assets")), name="assets")

    # SPA catch-all: any path not matched by an API route returns index.html
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        return FileResponse(str(_static / "index.html"))
