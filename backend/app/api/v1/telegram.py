"""
Telegram Bot API endpoints
"""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.services.ticket_service import ticket_service
from app.services.ai_service import ai_service
from app.core.config import settings

router = APIRouter()


class AnalyzeMessageRequest(BaseModel):
    """Request for message analysis"""
    text: str
    contact_info: Optional[Dict[str, Any]] = None


class AnalyzeMessageResponse(BaseModel):
    """Response for message analysis"""
    can_answer: bool
    answer: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    priority: str = "medium"
    department: Optional[str] = None
    subject: Optional[str] = None


class CreateTelegramTicketRequest(BaseModel):
    """Request for creating ticket from Telegram"""
    source: str = "telegram"
    subject: str
    text: str
    contact_info: Dict[str, Any]
    telegram_user_id: int
    telegram_chat_id: int
    telegram_username: Optional[str] = None


def verify_telegram_api_key(api_key: Optional[str] = Header(None, alias="X-Telegram-API-Key")) -> bool:
    """Verify Telegram bot API key"""
    expected_key = settings.TELEGRAM_BOT_API_KEY
    if not expected_key:
        # Если ключ не настроен, разрешаем (для разработки)
        return True
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    if api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


@router.post("/analyze", response_model=AnalyzeMessageResponse)
async def analyze_message(
    request: AnalyzeMessageRequest,
    api_key: Optional[str] = Header(None, alias="X-Telegram-API-Key")
) -> AnalyzeMessageResponse:
    """
    Analyze message using RAG/AI
    Returns whether we can answer immediately or need to create a ticket
    """
    # Verify API key
    verify_telegram_api_key(api_key)
    
    try:
        # Classify message
        classification = await ai_service.classify_ticket(request.text, "")
        
        # Retrieve knowledge base snippets
        kb_snippets = await ai_service.retrieve_kb(request.text, k=5)
        
        # Try to generate answer
        answer_result = await ai_service.generate_answer(
            request.text,
            classification["language"],
            kb_snippets
        )
        
        # Determine if we can answer based on confidence and answer quality
        answer_text = answer_result.get("answer", "")
        confidence = answer_result.get("confidence", 0.0)
        can_answer = confidence > 0.7 and len(answer_text) > 20 and not answer_result.get("need_on_site", False)
        
        # Get department
        department_name = classification.get("department", "TechSupport")
        
        return AnalyzeMessageResponse(
            can_answer=can_answer,
            answer=answer_text if can_answer else None,
            category=classification.get("category"),
            subcategory=classification.get("subcategory"),
            priority=classification.get("priority", "medium"),
            department=department_name,
            subject=request.text[:50] + "..." if len(request.text) > 50 else request.text
        )
    except Exception as e:
        # В случае ошибки создаем тикет
        return AnalyzeMessageResponse(
            can_answer=False,
            priority="medium",
            department="TechSupport",
            subject=request.text[:50] + "..." if len(request.text) > 50 else request.text
        )


@router.post("/create-ticket")
async def create_telegram_ticket(
    request: CreateTelegramTicketRequest,
    api_key: Optional[str] = Header(None, alias="X-Telegram-API-Key")
) -> Dict[str, Any]:
    """Create ticket from Telegram bot"""
    # Verify API key
    verify_telegram_api_key(api_key)
    
    try:
        ticket_data = {
            "source": request.source,
            "client_id": None,  # Will be created automatically if needed
            "subject": request.subject,
            "text": request.text,
            "incoming_meta": {
                "telegram_user_id": request.telegram_user_id,
                "telegram_chat_id": request.telegram_chat_id,
                "telegram_username": request.telegram_username,
                "contact_info": request.contact_info
            }
        }
        
        ticket = await ticket_service.create_ticket(ticket_data)
        
        # Process with AI
        ai_result = await ticket_service.process_with_ai(ticket["id"])
        
        return {
            "ticket_id": ticket["id"],
            "status": "created",
            "priority": ai_result.get("priority", "medium"),
            "department": ai_result.get("department_id"),
            "ai_processing": ai_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

