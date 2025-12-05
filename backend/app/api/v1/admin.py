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
    
    # Get chat interactions in period (для авторешений из публичного чата)
    interactions_result = supabase.table("chat_interactions")\
        .select("*")\
        .gte("created_at", from_date)\
        .lte("created_at", to_date)\
        .execute()
    
    interactions = interactions_result.data if interactions_result.data else []
    
    # Авторешения из тикетов
    auto_resolved_tickets = len([t for t in tickets if t.get("auto_resolved")])
    
    # Авторешения из chat_interactions (ticket_created = FALSE)
    auto_resolved_interactions = len([i for i in interactions if not i.get("ticket_created")])
    
    # Общая метрика авторешений
    total_auto_resolved = auto_resolved_tickets + auto_resolved_interactions
    total_requests = len(tickets) + len(interactions)
    auto_resolve_rate = (total_auto_resolved / total_requests * 100) if total_requests > 0 else 0.0
    
    print(f"[ADMIN METRICS] Auto-resolve:")
    print(f"  - Tickets: {len(tickets)} total, {auto_resolved_tickets} auto-resolved")
    print(f"  - Interactions: {len(interactions)} total, {auto_resolved_interactions} auto-resolved")
    print(f"  - Overall rate: {auto_resolve_rate:.2f}%")
    
    # SLA compliance
    # Для тикетов: считаем resolved/auto_resolved/closed
    sla_compliant_tickets = len([t for t in tickets if t.get("status") in ["resolved", "auto_resolved", "closed"]])
    
    # Для chat_interactions: считаем авторешения как SLA compliant (быстрый ответ без создания тикета)
    sla_compliant_interactions = auto_resolved_interactions
    
    total_sla_compliant = sla_compliant_tickets + sla_compliant_interactions
    sla_compliance = (total_sla_compliant / total_requests * 100) if total_requests > 0 else 0.0
    
    # Среднее время ответа из chat_interactions
    response_times = [
        i.get("response_time_ms", 0) / 1000.0 
        for i in interactions 
        if i.get("response_time_ms") is not None
    ]
    avg_response_time = sum(response_times) / len(response_times) if response_times else None
    
    # Classification Accuracy (из classification_feedback)
    feedback_result = supabase.table("classification_feedback")\
        .select("*")\
        .gte("feedback_at", from_date)\
        .lte("feedback_at", to_date)\
        .execute()
    
    feedbacks = feedback_result.data if feedback_result.data else []
    total_classifications = len(feedbacks)
    correct_classifications = len([f for f in feedbacks if f.get("is_correct")])
    classification_accuracy = (correct_classifications / total_classifications * 100) if total_classifications > 0 else None
    
    print(f"[ADMIN METRICS] Classification accuracy:")
    print(f"  - Total classifications: {total_classifications}")
    print(f"  - Correct: {correct_classifications}")
    print(f"  - Accuracy: {classification_accuracy:.2f}%" if classification_accuracy else "  - Accuracy: N/A")
    
    return MetricsResponse(
        total_tickets=total_requests,  # Общее количество запросов (тикеты + взаимодействия)
        auto_resolve_rate=auto_resolve_rate,
        sla_compliance=sla_compliance,
        classification_accuracy=classification_accuracy,  # Точность классификации из feedback
        avg_response_time=avg_response_time,  # Среднее время ответа из chat_interactions
        period_from=datetime.fromisoformat(from_date.replace('Z', '+00:00')),
        period_to=datetime.fromisoformat(to_date.replace('Z', '+00:00'))
    )

