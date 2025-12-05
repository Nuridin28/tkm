"""
WhatsApp Bot API endpoints with RAG integration
"""
from fastapi import APIRouter, HTTPException, Header, Body
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.services.ticket_service import ticket_service
from app.core.config import settings
from app.core.database import get_supabase_admin
from app.api.v1.public_chat import embed_query, extract_client_type, categorize_ticket
from datetime import datetime
import time
from openai import OpenAI

router = APIRouter()

# Инициализация OpenAI клиента
_openai_client = None

def get_openai_client():
    """Get OpenAI client instance"""
    global _openai_client
    if _openai_client is None:
        api_key = str(settings.OPENAI_API_KEY).strip()
        if not api_key or not api_key.startswith('sk-'):
            raise ValueError("Invalid OpenAI API key")
        _openai_client = OpenAI(api_key=api_key, timeout=60.0, max_retries=3)
    return _openai_client


class AnalyzeWhatsAppMessageRequest(BaseModel):
    """Request for WhatsApp message analysis"""
    text: str
    from_number: str
    conversation_history: Optional[List[Dict[str, Any]]] = []
    contact_info: Optional[Dict[str, Any]] = None


class AnalyzeWhatsAppMessageResponse(BaseModel):
    """Response for WhatsApp message analysis"""
    can_answer: bool
    answer: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    priority: str = "medium"
    department: Optional[str] = None
    subject: Optional[str] = None
    confidence: Optional[float] = None


class CreateWhatsAppTicketRequest(BaseModel):
    """Request for creating ticket from WhatsApp"""
    source: str = "whatsapp"
    subject: str
    text: str
    contact_info: Dict[str, Any]
    whatsapp_number: str


def verify_whatsapp_api_key(api_key: Optional[str] = Header(None, alias="X-WhatsApp-API-Key")) -> bool:
    """Verify WhatsApp bot API key"""
    expected_key = getattr(settings, 'WHATSAPP_BOT_API_KEY', None)
    if not expected_key:
        # Если ключ не настроен, разрешаем (для разработки)
        return True
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    if api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


@router.post("/analyze", response_model=AnalyzeWhatsAppMessageResponse)
async def analyze_whatsapp_message(
    request: AnalyzeWhatsAppMessageRequest,
    api_key: Optional[str] = Header(None, alias="X-WhatsApp-API-Key")
) -> AnalyzeWhatsAppMessageResponse:
    """
    Analyze WhatsApp message using RAG/AI (same logic as public_chat)
    Returns whether we can answer immediately or need to create a ticket
    """
    # Verify API key
    verify_whatsapp_api_key(api_key)
    
    start_time = time.time()
    
    try:
        # Normalize message
        message = str(request.text).strip()
        message = message.encode('utf-8', errors='ignore').decode('utf-8')
        
        # Build conversation history
        conversation_history = request.conversation_history or []
        
        # Extract client type
        client_type = extract_client_type(conversation_history)
        is_corporate = client_type == "corporate" if client_type else False
        
        # Create embedding for query
        try:
            query_emb = await embed_query(message)
        except Exception as e:
            print(f"Error creating embedding: {e}")
            # Fallback to simple classification
            from app.services.ai_service import ai_service
            classification = await ai_service.classify_ticket(message, "")
            return AnalyzeWhatsAppMessageResponse(
                can_answer=False,
                category=classification.get("category"),
                subcategory=classification.get("subcategory"),
                priority=classification.get("priority", "medium"),
                department=classification.get("department", "TechSupport"),
                subject=message[:50] + "..." if len(message) > 50 else message,
                confidence=0.0
            )
        
        # Search in knowledge base using RAG
        supabase = get_supabase_admin()
        kazakhtelecom_result = supabase.rpc(
            "match_documents",
            {
                "query_embedding": query_emb,
                "match_count": 6,
                "filter": {"source_type": "kazakhtelecom"}
            }
        ).execute()
        
        kazakhtelecom_chunks = kazakhtelecom_result.data or []
        
        # Build context
        context = ""
        max_similarity = 0.0
        if kazakhtelecom_chunks:
            # Filter chunks with reasonable similarity (>= 0.1) to avoid noise
            filtered_chunks = [chunk for chunk in kazakhtelecom_chunks if chunk.get('similarity', 0.0) >= 0.1]
            if not filtered_chunks:
                filtered_chunks = kazakhtelecom_chunks[:3]  # Use top 3 if all are below 0.1
            
            context += "ИНФОРМАЦИЯ ИЗ ДОКУМЕНТА КАЗАХТЕЛЕКОМ:\n\n"
            for i, chunk in enumerate(filtered_chunks):
                page_info = f"(Страница {chunk.get('metadata', {}).get('page', '?')})" if chunk.get('metadata', {}).get('page') else ""
                similarity = chunk.get('similarity', 0.0)
                if similarity > max_similarity:
                    max_similarity = similarity
                context += f"[Информация {i + 1}] {page_info} (релевантность: {similarity:.2f})\n{chunk.get('content', '')}\n\n"
        
        # Generate answer using OpenAI with RAG context
        if context:
            system_prompt = f"""Ты часть системы Help Desk Казахтелеком. Твоя основная задача — отвечать пользователю через RAG по базе знаний.

{"ТИП КЛИЕНТА: Корпоративный клиент\n\n" if is_corporate else ""}ВАЖНЫЕ ПРАВИЛА:
1. ВСЕГДА пытайся ответить на вопрос пользователя, используя информацию из предоставленных фрагментов документации
2. Если информация есть в фрагментах (даже частично) - используй её для формирования ответа
3. НЕ придумывай информацию - используй ТОЛЬКО то, что есть в предоставленных фрагментах
4. Отвечай на русском языке профессионально и понятно
5. Всегда указывай номер страницы при цитировании из документации
6. Будь вежливым и профессиональным
7. Для информационных вопросов (тарифы, условия, возможности) старайся дать полный ответ на основе доступной информации

ВАЖНО: Если у тебя есть информация из документации, даже если она не полностью покрывает вопрос - используй её для ответа. НЕ говори "нужно создать тикет" если можешь дать хотя бы частичный ответ на основе документации."""
            
            try:
                client = get_openai_client()
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"{context}\n\nВопрос пользователя: {message}"}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                
                answer_text = response.choices[0].message.content.strip()
                confidence = max_similarity if max_similarity > 0.2 else 0.1
                
                # Check if answer contains ticket request
                import re
                ticket_match = re.search(
                    r"\[TICKET_REQUIRED\]|создать тикет|нужен тикет|требуется тикет|обратитесь в техподдержку",
                    answer_text,
                    re.IGNORECASE
                )
                
                # Check for technical issues (only real technical problems requiring intervention)
                full_text_for_check = (message + " " + " ".join([m.get("content", "") for m in conversation_history])).lower()
                is_technical_issue = bool(re.search(
                    r"роутер не работает|модем не работает|оборудование сломалось|диагностика оборудования|техническая поломка|требуется ремонт|нужен выезд|помощь специалиста на месте|замена оборудования",
                    full_text_for_check
                ))
                
                # Check if it's an informational question (can be answered even with lower similarity)
                is_informational = bool(re.search(
                    r"могу ли|можно ли|как|что|где|когда|сколько|какие|какой|информац|узнать|расскажи|объясни|вопрос",
                    message.lower()
                ))
                
                # Determine similarity threshold based on question type
                # For informational questions, use lower threshold (0.15 instead of 0.2)
                similarity_threshold = 0.15 if is_informational else 0.2
                
                # Determine if we can answer
                # Can answer if:
                # 1. Have relevant information (similarity >= threshold)
                # 2. Answer is meaningful (length > 20)
                # 3. Answer doesn't explicitly request ticket
                # 4. Not a technical issue requiring physical intervention
                can_answer = (
                    max_similarity >= similarity_threshold and 
                    len(answer_text) > 20 and 
                    not ticket_match and
                    not is_technical_issue
                )
                
                print(f"[WHATSAPP ANALYZE] Question: '{message[:50]}...'")
                print(f"[WHATSAPP ANALYZE] max_similarity={max_similarity:.2f}, threshold={similarity_threshold:.2f}, is_informational={is_informational}, is_technical={is_technical_issue}")
                print(f"[WHATSAPP ANALYZE] can_answer={can_answer}, answer_length={len(answer_text)}")
                
                # Remove ticket request from answer if present
                if ticket_match:
                    answer_text = re.sub(r"\[TICKET_REQUIRED\][\s\S]*$", "", answer_text).strip()
                    answer_text = re.sub(r"создать тикет|нужен тикет|требуется тикет", "", answer_text, flags=re.IGNORECASE).strip()
                
                # Categorize ticket (for fallback)
                categorization = categorize_ticket(message, conversation_history, client_type or "private")
                
                print(f"[WHATSAPP ANALYZE] max_similarity={max_similarity:.2f}, can_answer={can_answer}, is_technical={is_technical_issue}, has_ticket_request={bool(ticket_match)}")
                
                return AnalyzeWhatsAppMessageResponse(
                    can_answer=can_answer,
                    answer=answer_text if can_answer else None,
                    category=categorization.get("category"),
                    subcategory=categorization.get("subcategory"),
                    priority=categorization.get("priority", "medium"),
                    department=categorization.get("department", "TechSupport"),
                    subject=message[:50] + "..." if len(message) > 50 else message,
                    confidence=confidence
                )
            except Exception as e:
                print(f"Error generating answer: {e}")
        
        # Fallback: no context or error
        categorization = categorize_ticket(message, conversation_history, client_type or "private")
        
        return AnalyzeWhatsAppMessageResponse(
            can_answer=False,
            category=categorization.get("category"),
            subcategory=categorization.get("subcategory"),
            priority=categorization.get("priority", "medium"),
            department=categorization.get("department", "TechSupport"),
            subject=message[:50] + "..." if len(message) > 50 else message,
            confidence=0.0
        )
        
    except Exception as e:
        print(f"Error in analyze_whatsapp_message: {e}")
        # В случае ошибки создаем тикет
        return AnalyzeWhatsAppMessageResponse(
            can_answer=False,
            priority="medium",
            department="TechSupport",
            subject=request.text[:50] + "..." if len(request.text) > 50 else request.text,
            confidence=0.0
        )


@router.post("/create-ticket")
async def create_whatsapp_ticket(
    request: CreateWhatsAppTicketRequest,
    api_key: Optional[str] = Header(None, alias="X-WhatsApp-API-Key")
) -> Dict[str, Any]:
    """Create ticket from WhatsApp bot"""
    # Verify API key
    verify_whatsapp_api_key(api_key)
    
    try:
        ticket_data = {
            "source": request.source,
            "client_id": None,  # Will be created automatically if needed
            "subject": request.subject,
            "text": request.text,
            "incoming_meta": {
                "whatsapp_number": request.whatsapp_number,
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

