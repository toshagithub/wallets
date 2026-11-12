import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.events.router import router as events_router
from app.auth.router import router as auth_router
from app.config.logging import configure_logging
from app.config.settings import settings
from app.wallet.apple.router import router as apple_wallet_router
from app.wallet.google.router import router as google_wallet_router
from app.ticket_types.router import router as ticket_types_router
from app.guests.router import router as guests_router
from app.passes.router import router as passes_router
from app.scanner.router import router as scanner_router

configure_logging()

logger = structlog.get_logger()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://93.115.22.90:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(apple_wallet_router)
app.include_router(google_wallet_router)
app.include_router(events_router)
app.include_router(ticket_types_router)
app.include_router(guests_router)
app.include_router(passes_router)
app.include_router(scanner_router)

@app.get("/health")
def health() -> dict[str, str]:
    logger.info("health_check")
    return {"status": "ok"}
