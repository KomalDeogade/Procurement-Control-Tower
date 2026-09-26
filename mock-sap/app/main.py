"""
Mock SAP Service – simulates SAP ERP endpoints for the prototype.

This is NOT a real SAP system.  It maintains in-memory transaction data
and returns realistic responses.  Replace with a real SAP adapter later
using the SAPAdapter interface in the main backend.
"""

from fastapi import FastAPI
from app.api.routes import router as sap_router

app = FastAPI(
    title="Mock SAP Service",
    description="Simulated SAP ERP endpoints for the SCM Procurement Control Tower prototype",
    version="0.1.0",
)

app.include_router(sap_router, prefix="/sap", tags=["SAP Simulation"])


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": "mock-sap",
        "version": "0.1.0",
        "note": "This is a simulated SAP service for prototype purposes only.",
    }
