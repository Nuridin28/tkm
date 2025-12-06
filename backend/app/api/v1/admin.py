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
    
    # ИСПРАВЛЕННАЯ ЛОГИКА: chat_interactions - это источник истины для всех запросов
    # tickets - это только те запросы, которые привели к созданию тикета
    
    # Получаем все взаимодействия (это все запросы пользователей)
    interactions_result = supabase.table("chat_interactions")\
        .select("*")\
        .gte("created_at", from_date)\
        .lte("created_at", to_date)\
        .execute()
    
    interactions = interactions_result.data if interactions_result.data else []
    total_requests = len(interactions)  # Все запросы = все взаимодействия
    
    # Авторешения = взаимодействия где ticket_created = FALSE или NULL
    auto_resolved_interactions = [
        i for i in interactions 
        if not i.get("ticket_created") or i.get("ticket_created") is False
    ]
    total_auto_resolved = len(auto_resolved_interactions)
    
    # Получаем созданные тикеты (для SLA compliance)
    tickets_result = supabase.table("tickets").select("*").gte("created_at", from_date).lte("created_at", to_date).execute()
    tickets = tickets_result.data if tickets_result.data else []
    total_tickets_created = len(tickets)
    
    # Авторешения из тикетов (старая логика, если есть)
    auto_resolved_tickets = len([t for t in tickets if t.get("auto_resolved")])
    
    # Общая метрика авторешений (только из chat_interactions, т.к. это источник истины)
    auto_resolve_rate = (total_auto_resolved / total_requests * 100) if total_requests > 0 else 0.0
    
    print(f"[ADMIN METRICS] Auto-resolve:")
    print(f"  - Total requests (interactions): {total_requests}")
    print(f"  - Auto-resolved (ticket_created=False): {total_auto_resolved}")
    print(f"  - Tickets created: {total_tickets_created}")
    print(f"  - Auto-resolve rate: {auto_resolve_rate:.2f}%")
    
    # SLA compliance
    # Для тикетов: считаем resolved/auto_resolved/closed
    sla_compliant_tickets = len([t for t in tickets if t.get("status") in ["resolved", "auto_resolved", "closed"]])
    
    # Для chat_interactions: считаем авторешения как SLA compliant (быстрый ответ без создания тикета)
    sla_compliant_interactions = total_auto_resolved
    
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
        total_tickets=total_requests,  # Общее количество запросов (все взаимодействия)
        auto_resolve_rate=auto_resolve_rate,
        sla_compliance=sla_compliance,
        classification_accuracy=classification_accuracy,  # Точность классификации из feedback
        avg_response_time=avg_response_time,  # Среднее время ответа из chat_interactions
        period_from=datetime.fromisoformat(from_date.replace('Z', '+00:00')),
        period_to=datetime.fromisoformat(to_date.replace('Z', '+00:00'))
    )

