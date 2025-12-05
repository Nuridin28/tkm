"""
Admin API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.schemas import MetricsResponse
from app.core.auth import require_role, get_current_user
from app.core.database import get_supabase_admin
from typing import Dict, Any
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    from_date: str = Query(None),
    to_date: str = Query(None),
    user: Dict[str, Any] = Depends(require_role(["admin", "supervisor"]))
) -> MetricsResponse:
    """Get admin metrics"""
    supabase = get_supabase_admin()
    
    # Default to last 30 days
    if not from_date:
        from_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
    if not to_date:
        to_date = datetime.utcnow().isoformat()
    
    # Get tickets in period
    tickets_result = supabase.table("tickets").select("*").gte("created_at", from_date).lte("created_at", to_date).execute()
    tickets = tickets_result.data if tickets_result.data else []
    
    total_tickets = len(tickets)
    auto_resolved = len([t for t in tickets if t.get("auto_resolved")])
    auto_resolve_rate = (auto_resolved / total_tickets * 100) if total_tickets > 0 else 0.0
    
    # SLA compliance (simplified)
    sla_compliant = len([t for t in tickets if t.get("status") in ["resolved", "auto_resolved", "closed"]])
    sla_compliance = (sla_compliant / total_tickets * 100) if total_tickets > 0 else 0.0
    
    return MetricsResponse(
        total_tickets=total_tickets,
        auto_resolve_rate=auto_resolve_rate,
        sla_compliance=sla_compliance,
        classification_accuracy=None,  # Would need feedback data
        avg_response_time=None,  # Would need message timestamps
        period_from=datetime.fromisoformat(from_date.replace('Z', '+00:00')),
        period_to=datetime.fromisoformat(to_date.replace('Z', '+00:00'))
    )

