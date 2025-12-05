"""
API v1 Router
"""
from fastapi import APIRouter
from app.api.v1 import ingest, tickets, ai, admin, users, departments, telegram

router = APIRouter()

router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
router.include_router(ai.router, prefix="/ai", tags=["ai"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
router.include_router(users.router, prefix="/admin", tags=["users"])
router.include_router(departments.router, prefix="/admin/departments", tags=["departments"])
router.include_router(telegram.router, prefix="/telegram", tags=["telegram"])
