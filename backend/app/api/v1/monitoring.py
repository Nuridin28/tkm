"""
Monitoring API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from app.core.auth import require_role, get_current_user
from app.core.database import get_supabase_admin
from app.models.schemas import (
    MonitoringMetrics,
    ClassificationAccuracy,
    AutoResolveStats,
    ResponseTimeStats,
    RoutingErrorStats
)
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/monitoring/metrics", response_model=MonitoringMetrics)
async def get_monitoring_metrics(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(require_role(["admin", "supervisor"]))
) -> MonitoringMetrics:
    """Get comprehensive monitoring metrics"""
    supabase = get_supabase_admin()
    
    # Default to last 30 days
    if not from_date:
        from_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
    if not to_date:
        to_date = datetime.utcnow().isoformat()
    
    # 1. Classification Accuracy
    feedback_result = supabase.table("classification_feedback")\
        .select("*")\
        .gte("feedback_at", from_date)\
        .lte("feedback_at", to_date)\
        .execute()
    
    feedbacks = feedback_result.data if feedback_result.data else []
    total_classifications = len(feedbacks)
    correct_classifications = len([f for f in feedbacks if f.get("is_correct")])
    accuracy_percentage = (correct_classifications / total_classifications * 100) if total_classifications > 0 else 0.0
    
    # By category
    by_category = {}
    for feedback in feedbacks:
        cat = feedback.get("predicted_category", "unknown")
        if cat not in by_category:
            by_category[cat] = {"correct": 0, "total": 0}
        by_category[cat]["total"] += 1
        if feedback.get("is_correct"):
            by_category[cat]["correct"] += 1
    
    by_category_percent = {k: (v["correct"] / v["total"] * 100) if v["total"] > 0 else 0 
                          for k, v in by_category.items()}
    
    # By department
    by_department = {}
    for feedback in feedbacks:
        dept = feedback.get("predicted_department", "unknown")
        if dept not in by_department:
            by_department[dept] = {"correct": 0, "total": 0}
        by_department[dept]["total"] += 1
        if feedback.get("is_correct"):
            by_department[dept]["correct"] += 1
    
    by_department_percent = {k: (v["correct"] / v["total"] * 100) if v["total"] > 0 else 0 
                            for k, v in by_department.items()}
    
    # 2. Auto-resolve Stats
    tickets_result = supabase.table("tickets")\
        .select("*")\
        .gte("created_at", from_date)\
        .lte("created_at", to_date)\
        .execute()
    
    tickets = tickets_result.data if tickets_result.data else []
    total_tickets = len(tickets)
    auto_resolved_tickets = [t for t in tickets if t.get("auto_resolved")]
    total_auto_resolved = len(auto_resolved_tickets)
    auto_resolve_rate = (total_auto_resolved / total_tickets * 100) if total_tickets > 0 else 0.0
    
    # Average confidence
    confidences = [t.get("classification_confidence", 0) for t in auto_resolved_tickets if t.get("classification_confidence")]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    
    # By category
    auto_by_category = {}
    for ticket in auto_resolved_tickets:
        cat = ticket.get("category", "unknown")
        auto_by_category[cat] = auto_by_category.get(cat, 0) + 1
    
    # 3. Response Time Stats
    response_times_result = supabase.table("response_times")\
        .select("*")\
        .gte("first_response_at", from_date)\
        .lte("first_response_at", to_date)\
        .execute()
    
    response_times = response_times_result.data if response_times_result.data else []
    times = [rt.get("response_time_seconds", 0) for rt in response_times if rt.get("response_time_seconds")]
    
    avg_response_time = sum(times) / len(times) if times else 0.0
    sorted_times = sorted(times) if times else []
    median_response_time = sorted_times[len(sorted_times) // 2] if sorted_times else 0.0
    p95_index = int(len(sorted_times) * 0.95) if sorted_times else 0
    p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else 0.0
    
    # By source
    by_source = {}
    for rt in response_times:
        ticket_id = rt.get("ticket_id")
        ticket = next((t for t in tickets if t["id"] == ticket_id), None)
        if ticket:
            source = ticket.get("source", "unknown")
            if source not in by_source:
                by_source[source] = []
            if rt.get("response_time_seconds"):
                by_source[source].append(rt["response_time_seconds"])
    
    by_source_avg = {k: sum(v) / len(v) if v else 0 for k, v in by_source.items()}
    
    # 4. Routing Errors
    routing_errors_result = supabase.table("routing_errors")\
        .select("*")\
        .gte("routed_at", from_date)\
        .lte("routed_at", to_date)\
        .execute()
    
    routing_errors = routing_errors_result.data if routing_errors_result.data else []
    total_routing_errors = len(routing_errors)
    error_rate = (total_routing_errors / total_tickets * 100) if total_tickets > 0 else 0.0
    
    # By error type
    by_error_type = {}
    for error in routing_errors:
        err_type = error.get("error_type", "unknown")
        by_error_type[err_type] = by_error_type.get(err_type, 0) + 1
    
    return MonitoringMetrics(
        classification_accuracy=ClassificationAccuracy(
            total_classifications=total_classifications,
            correct_classifications=correct_classifications,
            accuracy_percentage=accuracy_percentage,
            by_category=by_category_percent,
            by_department=by_department_percent
        ),
        auto_resolve_stats=AutoResolveStats(
            total_auto_resolved=total_auto_resolved,
            total_tickets=total_tickets,
            auto_resolve_rate=auto_resolve_rate,
            avg_confidence=avg_confidence,
            by_category=auto_by_category
        ),
        response_time_stats=ResponseTimeStats(
            avg_response_time_seconds=avg_response_time,
            median_response_time_seconds=median_response_time,
            p95_response_time_seconds=p95_response_time,
            by_source=by_source_avg,
            by_department={}  # Можно добавить по департаментам
        ),
        routing_error_stats=RoutingErrorStats(
            total_routing_errors=total_routing_errors,
            error_rate=error_rate,
            by_error_type=by_error_type,
            by_department={}  # Можно добавить по департаментам
        ),
        period_from=datetime.fromisoformat(from_date.replace('Z', '+00:00')),
        period_to=datetime.fromisoformat(to_date.replace('Z', '+00:00'))
    )

