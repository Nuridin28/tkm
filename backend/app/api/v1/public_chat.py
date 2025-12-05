"""
Public Chat API - для публичного обращения клиентов через ИИ-ассистента
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import PublicChatRequest, PublicChatResponse, PublicChatMessage
from app.services.ai_service import ai_service
from app.services.ticket_service import ticket_service
from typing import Dict, Any
from datetime import datetime
import json

router = APIRouter()


@router.post("/chat", response_model=PublicChatResponse)
async def public_chat(request: PublicChatRequest) -> PublicChatResponse:
    """
    Публичный чат с ИИ-ассистентом.
    
    Логика:
    1. Если ИИ знает ответ - возвращает его и спрашивает "Могу ли я чем-то помочь?"
    2. Если не знает - продолжает диалог, уточняет детали
    3. Если не может помочь - отправляет в RAG для классификации и создания драфта тикета
    """
    try:
        # Формируем контекст из истории диалога
        conversation_context = "\n".join([
            f"{msg.role}: {msg.content}" for msg in request.conversation_history
        ])
        full_message = f"{conversation_context}\nuser: {request.message}" if conversation_context else request.message
        
        # Сначала пытаемся найти ответ в базе знаний через RAG
        kb_results = await ai_service.retrieve_kb(full_message, k=3)
        
        # Генерируем ответ на основе найденной информации
        if kb_results:
            # Есть информация в базе знаний - пытаемся ответить
            answer_result = await ai_service.generate_answer(
                ticket_text=full_message,
                language="ru",  # TODO: определять язык автоматически
                kb_snippets=kb_results
            )
            
            # Если уверенность высокая - можем ответить
            if answer_result.get("confidence", 0) > 0.7:
                response_text = answer_result.get("answer", "")
                response_text += "\n\nМогу ли я чем-то еще помочь?"
                
                # Обновляем историю диалога
                updated_history = request.conversation_history.copy()
                updated_history.append(PublicChatMessage(
                    role="user",
                    content=request.message,
                    timestamp=datetime.now()
                ))
                updated_history.append(PublicChatMessage(
                    role="assistant",
                    content=response_text,
                    timestamp=datetime.now()
                ))
                
                return PublicChatResponse(
                    response=response_text,
                    can_answer=True,
                    needs_clarification=False,
                    should_create_ticket=False,
                    ticket_draft=None,
                    conversation_history=updated_history
                )
        
        # Если не нашли ответ или уверенность низкая - проверяем, нужны ли уточнения
        # Используем ИИ для определения, можем ли мы помочь или нужны уточнения
        clarification_prompt = f"""Ты - ассистент техподдержки. Проанализируй диалог и определи:
1. Можем ли мы ответить на вопрос клиента на основе имеющейся информации?
2. Нужны ли дополнительные уточнения от клиента?
3. Нужно ли создать тикет для передачи специалистам?

Диалог:
{full_message}

Ответь в формате JSON:
{{
    "can_answer": true/false,
    "needs_clarification": true/false,
    "clarification_question": "вопрос для уточнения (если нужен)",
    "should_create_ticket": true/false,
    "response": "ответ клиенту или вопрос для уточнения"
}}"""
        
        try:
            from openai import OpenAI
            from app.core.config import settings
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            model = settings.OPENAI_MODEL
            
            ai_response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Ты - ассистент техподдержки. Отвечай только валидным JSON."},
                    {"role": "user", "content": clarification_prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            
            ai_result = json.loads(ai_response.choices[0].message.content)
            
            can_answer = ai_result.get("can_answer", False)
            needs_clarification = ai_result.get("needs_clarification", False)
            should_create_ticket = ai_result.get("should_create_ticket", False)
            response_text = ai_result.get("response", "Спасибо за обращение. Я передам ваш вопрос специалистам.")
            
            # Обновляем историю диалога
            updated_history = request.conversation_history.copy()
            updated_history.append(PublicChatMessage(
                role="user",
                content=request.message,
                timestamp=datetime.now()
            ))
            updated_history.append(PublicChatMessage(
                role="assistant",
                content=response_text,
                timestamp=datetime.now()
            ))
            
            ticket_draft = None
            if should_create_ticket:
                # Классифицируем и создаем драфт тикета
                classification = await ai_service.classify_ticket(
                    ticket_text=full_message,
                    subject=request.message[:50]
                )
                
                # Генерируем краткое резюме
                summary = await ai_service.generate_summary(full_message, classification.get("language", "ru"))
                
                ticket_draft = {
                    "source": "portal",
                    "subject": request.message[:100] + ("..." if len(request.message) > 100 else ""),
                    "description": full_message,
                    "language": classification.get("language", "ru"),
                    "category": classification.get("category", "other"),
                    "subcategory": classification.get("subcategory", "general"),
                    "department": classification.get("department", "TechSupport"),
                    "priority": classification.get("priority", "medium"),
                    "summary": summary,
                    "contact_info": request.contact_info or {}
                }
            
            return PublicChatResponse(
                response=response_text,
                can_answer=can_answer,
                needs_clarification=needs_clarification,
                should_create_ticket=should_create_ticket,
                ticket_draft=ticket_draft,
                conversation_history=updated_history
            )
            
        except Exception as e:
            # Если ошибка при обращении к ИИ - создаем тикет
            classification = await ai_service.classify_ticket(
                ticket_text=full_message,
                subject=request.message[:50]
            )
            
            summary = await ai_service.generate_summary(full_message, classification.get("language", "ru"))
            
            ticket_draft = {
                "source": "portal",
                "subject": request.message[:100] + ("..." if len(request.message) > 100 else ""),
                "description": full_message,
                "language": classification.get("language", "ru"),
                "category": classification.get("category", "other"),
                "subcategory": classification.get("subcategory", "general"),
                "department": classification.get("department", "TechSupport"),
                "priority": classification.get("priority", "medium"),
                "summary": summary,
                "contact_info": request.contact_info or {}
            }
            
            return PublicChatResponse(
                response="Спасибо за обращение. Я передам ваш вопрос специалистам, они свяжутся с вами в ближайшее время.",
                can_answer=False,
                needs_clarification=False,
                should_create_ticket=True,
                ticket_draft=ticket_draft,
                conversation_history=request.conversation_history
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке запроса: {str(e)}")


@router.post("/chat/create-ticket")
async def create_ticket_from_chat(ticket_draft: Dict[str, Any]) -> Dict[str, Any]:
    """Создание тикета из драфта чата"""
    try:
        # Создаем тикет через ticket_service
        from app.models.schemas import TicketSource
        
        # Формируем описание с историей чата
        conversation_history = ticket_draft.get("conversation_history", [])
        description = ticket_draft.get("description", "")
        
        # Если есть история чата, добавляем её в описание
        if conversation_history:
            history_text = "\n\n=== История чата ===\n"
            for msg in conversation_history:
                role_name = "Клиент" if msg.get("role") == "user" else "ИИ-ассистент"
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")
                history_text += f"\n[{role_name}]: {content}\n"
            description = description + history_text
        
        ticket_data = {
            "source": TicketSource.PORTAL.value,
            "subject": ticket_draft.get("subject", "Обращение через чат"),
            "text": description,
            "incoming_meta": {
                "language": ticket_draft.get("language", "ru"),
                "category": ticket_draft.get("category", "other"),
                "subcategory": ticket_draft.get("subcategory", "general"),
                "department": ticket_draft.get("department", "TechSupport"),
                "priority": ticket_draft.get("priority", "medium"),
                "summary": ticket_draft.get("summary", ""),
                "conversation_history": conversation_history,  # Сохраняем историю в метаданных
                **ticket_draft.get("contact_info", {})
            }
        }
        
        result = await ticket_service.create_ticket(ticket_data)
        return {"success": True, "ticket_id": result.get("id"), "message": "Тикет успешно создан"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при создании тикета: {str(e)}")

