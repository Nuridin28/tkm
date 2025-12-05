"""
Tickets API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from app.models.schemas import TicketUpdateRequest, TicketResponse
from app.services.ticket_service import ticket_service
from app.services.ai_service import ai_service, get_openai_client
from app.core.auth import get_current_user, require_role
from app.core.database import get_supabase_admin
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

router = APIRouter()


@router.get("/auto-resolved")
async def get_auto_resolved_tickets(
    user: Dict[str, Any] = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> List[Dict[str, Any]]:
    """Get auto-resolved tickets from chat_interactions (where ticket_created=false)"""
    supabase = get_supabase_admin()
    
    # Get chat interactions where ticket_created = false (auto-resolved)
    # Используем правильный синтаксис Supabase для фильтрации
    try:
        # Сначала получаем все взаимодействия для отладки
        all_interactions_result = supabase.table("chat_interactions")\
            .select("id, ticket_created, message, ai_response, created_at")\
            .order("created_at", desc=True)\
            .limit(1000)\
            .execute()
        
        all_interactions = all_interactions_result.data or []
        print(f"[AUTO_RESOLVED] Total interactions in DB: {len(all_interactions)}")
        
        # Фильтруем в Python, так как Supabase может иметь проблемы с boolean фильтрацией
        interactions = [
            i for i in all_interactions 
            if i.get("ticket_created") is False or i.get("ticket_created") is None
        ]
        
        print(f"[AUTO_RESOLVED] Filtered auto-resolved interactions: {len(interactions)}")
        
        # Применяем пагинацию
        interactions = interactions[offset:offset + limit]
        
        # Получаем полные данные для отфильтрованных взаимодействий
        if interactions:
            interaction_ids = [i.get("id") for i in interactions]
            full_interactions_result = supabase.table("chat_interactions")\
                .select("*")\
                .in_("id", interaction_ids)\
                .execute()
            
            interactions = full_interactions_result.data or []
    except Exception as e:
        print(f"[AUTO_RESOLVED] Error fetching interactions: {e}")
        import traceback
        traceback.print_exc()
        interactions = []
    
    # Format as ticket-like objects for frontend
    auto_resolved = []
    for interaction in interactions:
        # Проверяем, что это действительно авторешение (ticket_created = False или NULL)
        ticket_created = interaction.get("ticket_created")
        if ticket_created is True:
            continue  # Пропускаем, если тикет был создан
        
        message = interaction.get("message", "")
        ai_response = interaction.get("ai_response", "")
        
        # Пропускаем пустые взаимодействия
        if not message or not ai_response:
            continue
        
        auto_resolved.append({
            "id": f"auto_{interaction.get('id')}",
            "type": "auto_resolved",
            "subject": message[:50] + "..." if len(message) > 50 else message,
            "description": message,
            "ai_response": ai_response,
            "category": interaction.get("category"),
            "subcategory": interaction.get("subcategory"),
            "department": interaction.get("department"),
            "priority": interaction.get("priority", "medium"),
            "status": "auto_resolved",
            "auto_resolved": True,
            "confidence": interaction.get("confidence", 0.0),
            "max_similarity": interaction.get("max_similarity", 0.0),
            "client_type": interaction.get("client_type"),
            "language": interaction.get("language", "ru"),
            "response_time_ms": interaction.get("response_time_ms", 0),
            "created_at": interaction.get("created_at"),
            "user_id": interaction.get("user_id"),
            "session_id": interaction.get("session_id"),
            "sources": interaction.get("sources", [])
        })
    
    print(f"[AUTO_RESOLVED] Returning {len(auto_resolved)} formatted auto-resolved tickets")
    return auto_resolved


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> TicketResponse:
    """Get ticket by ID"""
    ticket = await ticket_service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Проверяем права доступа: инженеры могут видеть только тикеты своего департамента
    supabase_admin = get_supabase_admin()
    user_id = user.get("id")
    if user_id:
        try:
            user_result = supabase_admin.table("users").select("role, department_id").eq("id", user_id).single().execute()
            if user_result.data:
                user_role = user_result.data.get("role")
                user_department_id = user_result.data.get("department_id")
                
                # Если пользователь - инженер, проверяем category
                if user_role == "engineer":
                    ticket_category = ticket.get("category", "").lower()
                    # Определяем category инженера по его департаменту
                    if user_department_id:
                        try:
                            dept_result = supabase_admin.table("departments").select("name").eq("id", user_department_id).single().execute()
                            if dept_result.data:
                                dept_name = dept_result.data.get("name", "").lower()
                                # Маппинг департаментов на категории
                                if "network" in dept_name:
                                    user_category = "network"
                                elif "billing" in dept_name:
                                    user_category = "billing"
                                elif "tech" in dept_name or "support" in dept_name:
                                    user_category = "technical"
                                else:
                                    user_category = dept_name
                                
                                if ticket_category != user_category:
                                    raise HTTPException(
                                        status_code=403,
                                        detail=f"You don't have permission to view this ticket. It belongs to category '{ticket_category}', but you can only see '{user_category}' tickets."
                                    )
                        except HTTPException:
                            raise
                        except Exception as e:
                            print(f"[GET_TICKET] Error checking engineer category: {e}")
                # Если пользователь не admin/supervisor и не engineer, проверяем департамент
                elif user_role not in ["admin", "supervisor"]:
                    ticket_department_id = ticket.get("department_id")
                    if ticket_department_id != user_department_id:
                        raise HTTPException(
                            status_code=403,
                            detail="You don't have permission to view this ticket. It belongs to a different department."
                        )
        except HTTPException:
            raise
        except Exception as e:
            print(f"[GET_TICKET] Error checking permissions: {e}")
            # В случае ошибки разрешаем доступ (fallback)
    
    return TicketResponse(**ticket)


@router.patch("/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    updates: TicketUpdateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update ticket (manual override)"""
    # Get current ticket to check for routing errors
    current_ticket = await ticket_service.get_ticket(ticket_id)
    if not current_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    update_dict = updates.model_dump(exclude_unset=True)
    
    # Convert enums to strings
    if "status" in update_dict:
        update_dict["status"] = update_dict["status"].value
    if "priority" in update_dict:
        update_dict["priority"] = update_dict["priority"].value
    
    # Log routing error if department changed
    if "department_id" in update_dict and update_dict["department_id"] != current_ticket.get("department_id"):
        await ticket_service._log_routing_error(
            ticket_id=ticket_id,
            initial_department_id=current_ticket.get("department_id"),
            correct_department_id=update_dict["department_id"],
            routed_by=user.get("id"),
            error_type="wrong_department"
        )
    
    ticket = await ticket_service.update_ticket(ticket_id, update_dict)
    return ticket


@router.post("/{ticket_id}/accept")
async def accept_ticket(
    ticket_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Accept ticket (agent action)"""
    # Get ticket to calculate response time
    ticket = await ticket_service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    now = datetime.utcnow()
    created_at = datetime.fromisoformat(ticket["created_at"].replace('Z', '+00:00'))
    response_time_seconds = int((now - created_at).total_seconds())
    
    updates = {
        "status": "accepted",
        "first_response_at": now.isoformat()
    }
    ticket = await ticket_service.update_ticket(ticket_id, updates)
    
    # Log response time
    await ticket_service._log_response_time(ticket_id, now, response_time_seconds, "human")
    
    return ticket


@router.post("/{ticket_id}/complete_remote")
async def complete_remote(
    ticket_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Mark ticket as resolved remotely"""
    updates = {"status": "resolved"}
    ticket = await ticket_service.update_ticket(ticket_id, updates)
    return ticket


@router.post("/{ticket_id}/request_on_site")
async def request_on_site(
    ticket_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Request on-site visit"""
    updates = {"need_on_site": True, "status": "on_site"}
    ticket = await ticket_service.update_ticket(ticket_id, updates)
    return ticket


@router.get("/{ticket_id}/messages")
async def get_messages(
    ticket_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get messages for a ticket"""
    supabase = get_supabase_admin()
    result = supabase.table("messages").select("*").eq("ticket_id", ticket_id).order("created_at").execute()
    return result.data if result.data else []


@router.get("")
async def list_tickets(
    department_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List tickets with filters"""
    from app.core.auth import get_user_role_from_db
    from app.core.database import get_supabase
    
    # Получаем роль пользователя
    supabase = get_supabase_admin()
    user_id = user.get("id")
    user_role = None
    
    if user_id:
        # Получаем роль и департамент из БД
        try:
            user_result = supabase.table("users").select("role, department_id").eq("id", user_id).single().execute()
            if user_result.data:
                user_role = user_result.data.get("role")
                user_department_id = user_result.data.get("department_id")
        except Exception as e:
            print(f"[LIST_TICKETS] Error getting user role: {e}")
            user_department_id = None
    else:
        user_department_id = None
    
    # Если пользователь - инженер, показываем только тикеты его категории
    if user_role == "engineer":
        # Для инженеров определяем category по department
        # Network department -> network category
        if user_department_id:
            try:
                dept_result = supabase.table("departments").select("name").eq("id", user_department_id).single().execute()
                if dept_result.data:
                    dept_name = dept_result.data.get("name", "").lower()
                    # Маппинг департаментов на категории
                    if "network" in dept_name:
                        category = "network"
                    elif "billing" in dept_name:
                        category = "billing"
                    elif "tech" in dept_name or "support" in dept_name:
                        category = "technical"
                    else:
                        category = dept_name  # Используем имя департамента как категорию
                    print(f"[LIST_TICKETS] Engineer {user_id} from department {dept_name} can only see tickets with category {category}")
            except Exception as e:
                print(f"[LIST_TICKETS] Error getting department name: {e}")
                return []
        else:
            print(f"[LIST_TICKETS] Engineer {user_id} has no department_id, returning empty list")
            return []
    # Если пользователь не admin/supervisor и не engineer, показываем только тикеты его департамента
    elif user_role not in ["admin", "supervisor"]:
        if user_department_id:
            # Принудительно устанавливаем фильтр по департаменту пользователя
            department_id = user_department_id
            print(f"[LIST_TICKETS] User {user_id} (role: {user_role}) can only see tickets from department {department_id}")
        else:
            # Если у пользователя нет департамента, не показываем тикеты
            print(f"[LIST_TICKETS] User {user_id} (role: {user_role}) has no department_id, returning empty list")
            return []
    
    tickets = await ticket_service.list_tickets(
        department_id=department_id,
        category=category,
        status=status,
        limit=limit,
        offset=offset
    )
    return tickets


@router.delete("/{ticket_id}")
async def delete_ticket(
    ticket_id: str,
    user: Dict[str, Any] = Depends(require_role(["admin", "supervisor"]))
) -> Dict[str, Any]:
    """Delete ticket (admin only)"""
    supabase = get_supabase_admin()
    try:
        # Удалить связанные сообщения
        supabase.table("messages").delete().eq("ticket_id", ticket_id).execute()
        # Удалить тикет
        result = supabase.table("tickets").delete().eq("id", ticket_id).execute()
        return {"success": True, "message": "Ticket deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to delete ticket: {str(e)}")


@router.post("/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: str,
    assigned_to: Optional[str] = None,
    department_id: Optional[str] = None,
    user: Dict[str, Any] = Depends(require_role(["admin", "supervisor"]))
) -> Dict[str, Any]:
    """Assign ticket to user or department (admin only)"""
    updates = {}
    if assigned_to:
        updates["assigned_to"] = assigned_to
    if department_id:
        updates["department_id"] = department_id
    if updates:
        updates["status"] = "accepted"
        ticket = await ticket_service.update_ticket(ticket_id, updates)
        return ticket
    raise HTTPException(status_code=400, detail="No assignment data provided")


@router.get("/{ticket_id}/ai-recommendations")
async def get_ai_recommendations(
    ticket_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get AI recommendations for ticket (response suggestions and solutions)"""
    ticket = await ticket_service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get chat history if ticket was created from chat
    supabase = get_supabase_admin()
    chat_interactions = []
    if ticket.get("source") == "chat":
        # Find chat interactions for this ticket
        interactions_result = supabase.table("chat_interactions")\
            .select("*")\
            .eq("ticket_id", ticket_id)\
            .order("created_at")\
            .execute()
        chat_interactions = interactions_result.data if interactions_result.data else []
    
    # Build context for AI
    ticket_text = f"Subject: {ticket.get('subject', '')}\n\nDescription: {ticket.get('description', '')}"
    if ticket.get("summary"):
        ticket_text += f"\n\nSummary: {ticket.get('summary')}"
    
    # Add chat history if available
    if chat_interactions:
        conversation_text = "\n\nИстория чата:\n"
        for interaction in chat_interactions:
            conversation_text += f"Пользователь: {interaction.get('message', '')}\n"
            conversation_text += f"Ассистент: {interaction.get('ai_response', '')}\n"
        ticket_text += conversation_text
    
    # Generate recommendations using AI
    try:
        client = get_openai_client()
        
        system_prompt = """Ты — ассистент техподдержки. На основе информации о тикете сформируй рекомендации для оператора:
1. Что ответить пользователю (краткий, понятный ответ)
2. Предложи решения для техподдержки (шаги для решения проблемы)

Выведи JSON с полями:
- user_response: текст ответа пользователю (2-3 предложения)
- support_solutions: массив строк с шагами решения проблемы
- confidence: уверенность в рекомендациях (0-1)"""
        
        response = client.chat.completions.create(
            model=ai_service.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": ticket_text}
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            "ticket_id": ticket_id,
            "user_response": result.get("user_response", ""),
            "support_solutions": result.get("support_solutions", []),
            "confidence": float(result.get("confidence", 0.5))
        }
    except Exception as e:
        print(f"Error generating AI recommendations: {e}")
        return {
            "ticket_id": ticket_id,
            "user_response": "Спасибо за обращение. Мы рассмотрим вашу заявку в ближайшее время.",
            "support_solutions": ["Проверить детали проблемы", "Связаться с клиентом для уточнений"],
            "confidence": 0.0
        }


@router.get("/{ticket_id}/chat-history")
async def get_chat_history(
    ticket_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get formatted chat history for ticket"""
    ticket = await ticket_service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    supabase = get_supabase_admin()
    
    # Get chat interactions for this ticket
    interactions_result = supabase.table("chat_interactions")\
        .select("*")\
        .eq("ticket_id", ticket_id)\
        .order("created_at")\
        .execute()
    
    interactions = interactions_result.data if interactions_result.data else []
    
    # Initialize formatted_history
    formatted_history = []
    
    # If no interactions found, try to find by session_id or user_id
    if not interactions and (ticket.get("source") == "chat" or ticket.get("source") == "portal"):
        # Try to find by source_meta
        source_meta = ticket.get("source_meta", {})
        if isinstance(source_meta, str):
            import json
            try:
                source_meta = json.loads(source_meta)
            except:
                source_meta = {}
        
        session_id = source_meta.get("session_id")
        user_id = source_meta.get("user_id")
        
        print(f"[CHAT_HISTORY] Looking for history: ticket_id={ticket_id}, session_id={session_id}, user_id={user_id}")
        
        if session_id:
            interactions_result = supabase.table("chat_interactions")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("created_at")\
                .execute()
            interactions = interactions_result.data if interactions_result.data else []
            print(f"[CHAT_HISTORY] Found {len(interactions)} interactions by session_id")
        elif user_id:
            interactions_result = supabase.table("chat_interactions")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at")\
                .execute()
            interactions = interactions_result.data if interactions_result.data else []
            print(f"[CHAT_HISTORY] Found {len(interactions)} interactions by user_id")
        
        # Also try to get conversation_history from source_meta if available
        if not interactions and source_meta.get("conversation_history"):
            conversation_history = source_meta.get("conversation_history", [])
            if isinstance(conversation_history, list):
                for msg in conversation_history:
                    formatted_history.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                        "timestamp": msg.get("timestamp")
                    })
                print(f"[CHAT_HISTORY] Using conversation_history from source_meta: {len(formatted_history)} messages")
                return formatted_history
    
    # Format history from interactions
    for interaction in interactions:
        # Add user message
        formatted_history.append({
            "role": "user",
            "content": interaction.get("message", ""),
            "timestamp": interaction.get("created_at")
        })
        # Add assistant response
        formatted_history.append({
            "role": "assistant",
            "content": interaction.get("ai_response", ""),
            "timestamp": interaction.get("created_at")
        })
    
    print(f"[CHAT_HISTORY] Returning {len(formatted_history)} formatted messages")
    return formatted_history


@router.post("/{ticket_id}/classify-feedback")
async def submit_classification_feedback(
    ticket_id: str,
    feedback: Dict[str, Any] = Body(...),
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Submit classification feedback (approve or change classification)"""
    ticket = await ticket_service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    supabase = get_supabase_admin()
    
    # Get predicted values from ticket
    predicted_category = ticket.get("category")
    predicted_department_id = ticket.get("department_id")
    predicted_priority = ticket.get("priority")
    confidence_score = ticket.get("classification_confidence", 0.0)
    
    # Get actual values from feedback (if changed)
    actual_category = feedback.get("category", predicted_category)
    actual_department_id = feedback.get("department_id", predicted_department_id)
    actual_priority = feedback.get("priority", predicted_priority)
    is_correct = feedback.get("is_correct", True)  # True if approved, False if changed
    notes = feedback.get("notes", "")
    
    # If department name is provided instead of ID, get department_id
    if actual_department_id and not isinstance(actual_department_id, str) or len(actual_department_id) < 36:
        # Might be department name, try to find by name
        dept_result = supabase.table("departments").select("id").eq("name", actual_department_id).execute()
        if dept_result.data:
            actual_department_id = dept_result.data[0]["id"]
    
    # Determine if classification is correct
    if not is_correct:
        # Classification was changed, so it was incorrect
        is_correct = False
    else:
        # Check if values match
        is_correct = (
            actual_category == predicted_category and
            actual_department_id == predicted_department_id and
            actual_priority == predicted_priority
        )
    
    # Save feedback
    feedback_data = {
        "ticket_id": ticket_id,
        "predicted_category": predicted_category,
        "predicted_department": predicted_department_id,
        "predicted_priority": predicted_priority,
        "actual_category": actual_category,
        "actual_department": actual_department_id,
        "actual_priority": actual_priority,
        "confidence_score": confidence_score,
        "feedback_by": user.get("id"),
        "is_correct": is_correct,
        "notes": notes
    }
    
    result = supabase.table("classification_feedback").insert(feedback_data).execute()
    
    # Update ticket: set status to in_progress, assign to department, and update classification
    update_data = {
        "status": "in_progress",  # Меняем статус с "new" на "in_progress"
        "department_id": actual_department_id  # Автоматически назначаем в отдел
    }
    
    # Update category, priority if changed
    if actual_category != predicted_category:
        update_data["category"] = actual_category
    if actual_priority != predicted_priority:
        update_data["priority"] = actual_priority
    
    # Log routing error if department or category changed
    if actual_department_id != predicted_department_id or actual_category != predicted_category:
        error_type = "wrong_department" if actual_department_id != predicted_department_id else "wrong_category"
        await ticket_service._log_routing_error(
            ticket_id=ticket_id,
            initial_department_id=predicted_department_id,
            correct_department_id=actual_department_id,
            routed_by=user.get("id"),
            error_type=error_type
        )
        print(f"[CLASSIFY_FEEDBACK] Routing error logged: {error_type} for ticket {ticket_id}")
    
    # Update ticket
    await ticket_service.update_ticket(ticket_id, update_data)
    
    print(f"[CLASSIFY_FEEDBACK] Ticket {ticket_id} updated: status=in_progress, is_correct={is_correct}")
    
    return {
        "success": True,
        "feedback_id": result.data[0]["id"] if result.data else None,
        "is_correct": is_correct,
        "ticket_updated": True
    }
