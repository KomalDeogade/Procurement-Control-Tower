"""
SCM Procurement Control Tower – FastAPI Application Entry Point.

Business rules live here in the backend, not in n8n or the frontend.
AI is advisory only — deterministic engines are the source of truth.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.session import Base, engine, async_session_maker
from app.services.auth_service import seed_default_users

from app.api import (
    auth,
    requirements,
    suppliers,
    quotes,
    approvals,
    purchase_orders,
    inventory,
    goods_receipts,
    invoices,
    payments,
    dashboard,
    audit,
)
from app.api import rfqs
from app.api import ai_features
from app.api import exceptions_monitor
from app.api import reports
from app.api import demo


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # Import all models so Base.metadata knows about them
    import app.models  # noqa: F401

    # Create all tables (for SQLite local dev)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default users on first run
    async with async_session_maker() as session:
        await seed_default_users(session)

    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-enabled Supply Chain Management Procurement Control Tower — Phase 3",
    version="0.3.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Core Routers ──────────────────────────────────────────────
app.include_router(auth.router,            prefix="/api/auth",            tags=["Authentication"])
app.include_router(requirements.router,    prefix="/api/requirements",    tags=["Requirements"])
app.include_router(suppliers.router,       prefix="/api/suppliers",       tags=["Suppliers"])
app.include_router(rfqs.router,            prefix="/api/rfqs",            tags=["RFQs"])
app.include_router(quotes.router,          prefix="/api/quotes",          tags=["Quotes"])
app.include_router(approvals.router,       prefix="/api/approvals",       tags=["Approvals"])
app.include_router(purchase_orders.router, prefix="/api/purchase-orders", tags=["Purchase Orders"])
app.include_router(inventory.router,       prefix="/api/inventory",       tags=["Inventory"])
app.include_router(goods_receipts.router,  prefix="/api/goods-receipts",  tags=["Goods Receipts"])
app.include_router(invoices.router,        prefix="/api/invoices",        tags=["Invoices"])
app.include_router(payments.router,        prefix="/api/payments",        tags=["Payments"])
app.include_router(dashboard.router,       prefix="/api/dashboard",       tags=["Dashboard"])
app.include_router(audit.router,           prefix="/api/audit",           tags=["Audit Log"])

# ── Phase 3: AI + Automation Routers ────────────────────────
app.include_router(ai_features.router,       prefix="/api/ai",         tags=["AI Features"])
app.include_router(exceptions_monitor.router, prefix="/api/exceptions", tags=["Exceptions & Monitoring"])
app.include_router(reports.router,           prefix="/api/reports",    tags=["Reports"])
app.include_router(demo.router,              prefix="/api/demo",       tags=["Demo Mode"])


# ── Health Check ─────────────────────────────────────────────
@app.get("/api/health", tags=["System"])
async def health_check():
    from app.services.ai_service import ai_service
    return {
        "status": "healthy",
        "service": "scm-backend",
        "version": "0.3.0",
        "ai_provider": ai_service.provider,
        "ai_available": ai_service.is_available,
    }
