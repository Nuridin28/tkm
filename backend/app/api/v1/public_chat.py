"""
Public Chat API - для публичного обращения клиентов через ИИ-ассистента с RAG
Интегрировано с логикой из call_helper
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import PublicChatRequest, PublicChatResponse, PublicChatMessage, SourceInfo
from app.services.ticket_service import ticket_service
from app.core.database import get_supabase_admin
from app.core.config import settings
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re
from openai import OpenAI

router = APIRouter()

# Инициализация OpenAI клиента
_openai_client = None

def get_openai_client():
    """Get OpenAI client instance"""
    global _openai_client
    if _openai_client is None:
        # Получаем API ключ из настроек
        api_key = str(settings.OPENAI_API_KEY).strip()
        
        # Валидация API ключа
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")
        
        if not api_key.startswith('sk-'):
            raise ValueError(f"Invalid OpenAI API key format. Key should start with 'sk-'. Got: {api_key[:10]}...")
        
        if len(api_key) < 20:
            raise ValueError(f"OpenAI API key seems too short. Expected at least 20 characters, got {len(api_key)}")
        
        # Проверяем, что ключ содержит только ASCII символы (но не удаляем их!)
        try:
            api_key.encode('ascii')
        except UnicodeEncodeError as e:
            # Если есть не-ASCII символы, это проблема - не удаляем их, а сообщаем об ошибке
            raise ValueError(f"OpenAI API key contains non-ASCII characters. Please check your .env file. Error: {e}")
        
        _openai_client = OpenAI(
            api_key=api_key,
            timeout=60.0,
            max_retries=3
        )
    return _openai_client


async def embed_query(query: str) -> List[float]:
    """Создать embedding для запроса"""
    # Нормализуем строку и убеждаемся, что это валидная UTF-8 строка
    if not isinstance(query, str):
        query = str(query)
    
    # Убираем возможные проблемы с кодировкой
    query = query.encode('utf-8', errors='ignore').decode('utf-8')
    
    client = get_openai_client()
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    return resp.data[0].embedding


def extract_client_type(history: List[Dict[str, Any]]) -> Optional[str]:
    """Извлечь тип клиента из истории разговора"""
    full_text = " ".join([m.get("content", "") for m in history]).lower()
    
    # Ключевые слова для корпоративных клиентов
    corporate_keywords = [
        "да", "корпоратив", "корпоративный", "корпоративный клиент", 
        "бизнес", "компания", "организация", "юридическое лицо", "юр. лицо"
    ]
    
    # Ключевые слова для отрицательных ответов
    negative_keywords = [
        "нет", "не корпоратив", "не являюсь корпоративным", "не корпоративный"
    ]
    
    # Сначала проверяем отрицательные ответы
    for keyword in negative_keywords:
        if keyword in full_text:
            return "private"
    
    # Затем проверяем корпоративные индикаторы
    for keyword in corporate_keywords:
        if keyword in full_text:
            return "corporate"
    
    return None


def categorize_ticket(
    message: str, 
    history: List[Dict[str, Any]], 
    client_type: str
) -> Dict[str, Any]:
    """Категоризация тикета на основе содержимого"""
    full_text = (message + " " + " ".join([m.get("content", "") for m in history])).lower()
    
    category = "other"
    subcategory = ""
    department = "TechSupport"
    priority = "medium"
    
    # Проблемы с сетью
    if re.search(r"интернет|интернета|подключ|соединен|связь|сеть|network|internet|wi-fi|wifi", full_text):
        category = "network"
        if re.search(r"скорост|медлен|тормоз|lag|speed", full_text):
            subcategory = "internet_speed"
            priority = "high"
        elif re.search(r"нет интернет|не работает|отключ|disconnect", full_text):
            subcategory = "connection_issue"
            priority = "critical"
        elif re.search(r"vpn|випиэн", full_text):
            subcategory = "vpn_access"
            department = "Network"
        else:
            subcategory = "general_network"
    
    # Телефония
    elif re.search(r"телефон|звонок|звонки|telephony|call|phone", full_text):
        category = "telephony"
        if re.search(r"не звон|не работает|не могу позвонить", full_text):
            subcategory = "call_issue"
            priority = "high"
        else:
            subcategory = "general_telephony"
    
    # TV
    elif re.search(r"телевизор|тв|tv|канал|каналы|программа", full_text):
        category = "tv"
        if re.search(r"не работает|нет сигнал|не показывает", full_text):
            subcategory = "signal_issue"
            priority = "high"
        else:
            subcategory = "general_tv"
    
    # Биллинг
    elif re.search(r"оплат|платеж|счет|биллинг|billing|тариф|цена|стоимость|деньги", full_text):
        category = "billing"
        department = "Billing"
        if re.search(r"не могу оплат|проблем|ошибк|не проходит", full_text):
            subcategory = "payment_issue"
            priority = "high"
        else:
            subcategory = "general_billing"
    
    # Оборудование
    elif re.search(r"оборудован|роутер|модем|устройств|equipment|device", full_text):
        category = "equipment"
        if re.search(r"не работает|сломал|поломк|замен", full_text):
            subcategory = "equipment_failure"
            priority = "high"
        else:
            subcategory = "general_equipment"
    
    # Корректировка приоритета
    if re.search(r"срочно|критич|критическ|urgent|critical|не работает|полностью", full_text):
        priority = "critical"
    elif re.search(r"важно|important|проблем|problem", full_text):
        priority = "high"
    elif re.search(r"вопрос|информац|уточнени|question", full_text):
        priority = "low"
    
    # Корпоративные клиенты получают высокий приоритет
    if client_type == "corporate" and priority != "critical":
        priority = "high"
    
    return {"category": category, "subcategory": subcategory, "department": department, "priority": priority}


async def create_ticket_from_chat(
    user_id: str,
    client_type: str,
    language: str,
    category: str,
    subcategory: str,
    department: str,
    priority: str,
    confidence: float,
    content: str
) -> Dict[str, Any]:
    """Создать тикет из чата"""
    from app.models.schemas import TicketSource
    
    ticket_data = {
        "source": TicketSource.CHAT.value,
        "subject": content[:100] + ("..." if len(content) > 100 else ""),
        "text": content,
        "incoming_meta": {
            "user_id": user_id,
            "client_type": client_type,
            "language": language,
            "category": category,
            "subcategory": subcategory,
            "department": department,
            "priority": priority,
            "confidence": confidence
        }
    }
    
    result = await ticket_service.create_ticket(ticket_data)
    return result


@router.post("/chat", response_model=PublicChatResponse)
async def public_chat(request: PublicChatRequest) -> PublicChatResponse:
    """
    Публичный чат с ИИ-ассистентом с RAG из call_helper.
    
    Логика:
    1. Определение типа клиента (корпоративный/частный)
    2. RAG поиск в базе знаний (таблица chunks)
    3. Генерация ответа с использованием найденной информации
    4. Создание тикета при необходимости
    5. Сохранение взаимодействия для метрик
    """
    import time
    start_time = time.time()
    
    try:
        # Нормализуем сообщение и убеждаемся, что это валидная UTF-8 строка
        message = str(request.message).strip()
        message = message.encode('utf-8', errors='ignore').decode('utf-8')
        
        conversation_history = [
            {
                "role": str(msg.role),
                "content": str(msg.content).encode('utf-8', errors='ignore').decode('utf-8')
            } 
            for msg in request.conversation_history
        ]
        user_id = request.contact_info.get("phone", "anonymous") if request.contact_info else "anonymous"
        language = "ru"  # TODO: определять язык автоматически
        
        # Генерируем session_id для группировки взаимодействий одного пользователя
        import time
        session_id = request.contact_info.get("session_id") if request.contact_info else f"session_{user_id}_{int(time.time())}"
        
        if not message:
            raise HTTPException(status_code=400, detail="Пустой запрос")
        
        # Проверяем тип клиента
        client_type = extract_client_type(conversation_history)
        
        # Если тип клиента неизвестен, спрашиваем
        if not client_type:
            return PublicChatResponse(
                response="Вы корпоративный клиент?",
                answer="Вы корпоративный клиент?",
                can_answer=False,
                needs_clarification=True,
                should_create_ticket=False,
                requiresClientType=True,
                conversation_history=request.conversation_history + [
                    PublicChatMessage(role="user", content=message, timestamp=datetime.now()),
                    PublicChatMessage(role="assistant", content="Вы корпоративный клиент?", timestamp=datetime.now())
                ]
            )
        
        is_corporate = client_type == "corporate"
        
        # 1) Создаем embedding для запроса
        try:
            query_emb = await embed_query(message)
        except ValueError as e:
            # Ошибка валидации API ключа
            print(f"API Key validation error: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Ошибка конфигурации OpenAI API ключа. Проверьте файл .env. Детали: {str(e)}"
            )
        except UnicodeEncodeError as e:
            # Если ошибка кодировки, логируем и пробуем еще раз с нормализованной строкой
            print(f"Unicode error in embed_query: {e}")
            # Дополнительная нормализация
            message_normalized = message.encode('utf-8', errors='replace').decode('utf-8')
            query_emb = await embed_query(message_normalized)
        except Exception as e:
            error_msg = str(e)
            # Проверяем, не связана ли ошибка с API ключом
            if "invalid_api_key" in error_msg.lower() or "401" in error_msg:
                print(f"OpenAI API authentication error: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Ошибка аутентификации OpenAI API. Проверьте правильность API ключа в файле .env (OPENAI_API_KEY)"
                )
            print(f"Error creating embedding: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка при создании embedding: {str(e)}")
        
        # 2) Ищем в базе знаний через match_documents
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
        
        # 3) Формируем контекст
        context = ""
        if kazakhtelecom_chunks:
            context += "ИНФОРМАЦИЯ ИЗ ДОКУМЕНТА КАЗАХТЕЛЕКОМ:\n\n"
            for i, chunk in enumerate(kazakhtelecom_chunks):
                page_info = f"(Страница {chunk.get('metadata', {}).get('page', '?')})" if chunk.get('metadata', {}).get('page') else ""
                similarity = f"(релевантность: {chunk.get('similarity', 0):.2f})" if chunk.get('similarity') else ""
                context += f"[Информация {i + 1}] {page_info} {similarity}\n{chunk.get('content', '')}\n\n"
        
        if not context:
            return PublicChatResponse(
                response="К сожалению, я не нашел информацию по вашему запросу. Попробуйте переформулировать вопрос.",
                answer="К сожалению, я не нашел информацию по вашему запросу. Попробуйте переформулировать вопрос.",
                can_answer=False,
                sources=[],
                confidence=0.0,
                conversation_history=request.conversation_history + [
                    PublicChatMessage(role="user", content=message, timestamp=datetime.now()),
                    PublicChatMessage(
                    role="assistant",
                        content="К сожалению, я не нашел информацию по вашему запросу. Попробуйте переформулировать вопрос.",
                    timestamp=datetime.now()
                    )
                ]
            )
        
        # 4) Формируем системный промпт
        system_prompt = f"""Ты часть системы Help Desk Казахтелеком. Твоя основная задача — отвечать пользователю через RAG по базе знаний.

{"ТИП КЛИЕНТА: Корпоративный клиент\n\n" if is_corporate else ""}ВАЖНЫЕ ПРАВИЛА:
1. ВСЕГДА сначала пытайся ответить самостоятельно через RAG, используя информацию из предоставленных фрагментов документации
2. НЕ придумывай информацию - используй ТОЛЬКО то, что есть в предоставленных фрагментах
3. Анализируй историю разговора - используй информацию, которую пользователь уже предоставил
4. Отвечай на русском языке профессионально и понятно
5. Всегда указывай номер страницы при цитировании из документации
6. При упоминании конкретных данных (тарифы, условия, требования) всегда указывай ТОЧНЫЕ данные из предоставленных фрагментов
7. Будь вежливым и профессиональным

ФОРМАТИРОВАНИЕ ОТВЕТА (используй Markdown):
- Используй заголовки (##) для разделения основных разделов
- Используй нумерованные списки (1., 2., 3.) для пошаговых инструкций
- Используй маркированные списки (- или *) для перечисления
- Используй **жирный текст** для выделения важной информации
- Используй *курсив* для акцента
- Используй `код` для номеров телефонов, кодов и т.д.
- Структурируй информацию для лучшей читаемости
- Добавляй пустые строки между разделами для лучшей читаемости

ВАЖНО - ФОРМАТ ОТВЕТА:
- Отвечай ТОЛЬКО текстом ответа пользователю
- НЕ добавляй в ответ технические метаданные (CONFIDENCE, NEEDS_TICKET и т.д.)
- НЕ добавляй в ответ информацию о тикетах, если можешь ответить
- Если информации достаточно - просто дай ответ
- Если информации недостаточно или требуется вмешательство - используй формат:
  [TICKET_REQUIRED]
  CONFIDENCE: <число>
  NEEDS_TICKET: true
  REASON: <объяснение>
  
НО: Если можешь дать ответ на основе документации - НЕ используй [TICKET_REQUIRED], просто ответь."""
        
        # 5) Формируем сообщения с историей
        messages = [{"role": "system", "content": system_prompt}]
        
        # Добавляем последние 10 сообщений из истории
        recent_history = conversation_history[-10:]
        for msg in recent_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Добавляем текущий запрос с контекстом
        messages.append({
            "role": "user",
            "content": f"ВОПРОС: {message}\n\n{context}\n\nОТВЕТЬ на вопрос, используя ТОЛЬКО информацию из предоставленных выше фрагментов документации Казахтелеком. Используй Markdown для форматирования. Если информации недостаточно или требуется вмешательство - укажи [TICKET_REQUIRED] с CONFIDENCE и REASON."
        })
        
        # 6) Получаем ответ от OpenAI
        client = get_openai_client()
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            messages=messages,
            max_tokens=2000
        )
        
        answer = completion.choices[0].message.content or ""
        
        # Проверяем максимальную релевантность
        max_similarity = max([c.get("similarity", 0) for c in kazakhtelecom_chunks]) if kazakhtelecom_chunks else 0
        
        # Удаляем упоминания типа клиента для частных клиентов
        if not is_corporate:
            client_type_mentions = [
                "для частных лиц", "для частных клиентов", "частным лицам",
                "для корпоративных", "корпоративным", "корпоративных клиентов"
            ]
            for mention in client_type_mentions:
                answer = re.sub(mention, "", answer, flags=re.IGNORECASE).strip()
            answer = re.sub(r"\s+", " ", answer).strip()
        
        # Удаляем блоки источников из ответа
        answer = re.sub(r"\n\n---\s*\n\nИсточники:[\s\S]*$", "", answer, flags=re.IGNORECASE).strip()
        answer = re.sub(r"\[Информация\s+\d+\]\s*\(Страница\s+\d+\)", "", answer, flags=re.IGNORECASE).strip()
        
        # Удаляем технические метаданные, которые ИИ мог добавить в ответ
        answer = re.sub(r"\n*\s*CONFIDENCE:\s*[\d.]+\s*", "", answer, flags=re.IGNORECASE).strip()
        answer = re.sub(r"\n*\s*NEEDS_TICKET:\s*(true|false)\s*", "", answer, flags=re.IGNORECASE).strip()
        answer = re.sub(r"\n*\s*REASON:\s*[^\n]*", "", answer, flags=re.IGNORECASE).strip()
        answer = re.sub(r"CONFIDENCE:\s*[\d.]+", "", answer, flags=re.IGNORECASE).strip()
        answer = re.sub(r"NEEDS_TICKET:\s*(true|false)", "", answer, flags=re.IGNORECASE).strip()
        
        # Очищаем от лишних пробелов и переносов строк
        answer = re.sub(r"\n{3,}", "\n\n", answer)  # Убираем множественные переносы
        answer = re.sub(r"[ \t]+", " ", answer)  # Убираем множественные пробелы
        answer = answer.strip()
        
        # Парсим требование тикета
        ticket_match = re.search(
            r"\[TICKET_REQUIRED\]\s*CONFIDENCE:\s*([\d.]+)\s*NEEDS_TICKET:\s*(true|false)\s*REASON:\s*([\s\S]+?)(?=\n\n|\n$|$)",
            answer
        )
        
        needs_ticket = False
        confidence = 0.0
        ticket_reason = ""
        ai_explicitly_requested_ticket = False
        
        if ticket_match:
            needs_ticket = ticket_match.group(2) == "true"
            ai_explicitly_requested_ticket = needs_ticket  # Запоминаем, что AI явно запросил тикет
            confidence = float(ticket_match.group(1)) if ticket_match.group(1) else 0.0
            ticket_reason = ticket_match.group(3).strip() if ticket_match.group(3) else ""
            
            print(f"[TICKET LOGIC] AI explicitly requested ticket: {needs_ticket}, confidence: {confidence}, reason: {ticket_reason[:100]}")
            
            # Удаляем блок тикета из ответа
            answer = re.sub(r"\[TICKET_REQUIRED\][\s\S]*$", "", answer).strip()
        else:
            # Вычисляем уверенность на основе релевантности
            if max_similarity >= 0.2:
                confidence = max(0.2, max_similarity)
            else:
                confidence = max_similarity
            print(f"[TICKET LOGIC] No explicit ticket request, max_similarity: {max_similarity}, confidence: {confidence}")
        
        # Проверяем, нужно ли создавать тикет
        full_text_for_check = (message + " " + ticket_reason + " " + " ".join([m.get("content", "") for m in conversation_history])).lower()
        is_technical_issue = bool(re.search(
            r"роутер|модем|оборудован|диагностик|техническ|не работает|сломал|поломк|замен|техническая проблема|помощь специалиста|требуется вмешательство|выезд|ремонт",
            full_text_for_check
        ))
        
        print(f"[TICKET LOGIC] max_similarity: {max_similarity}, is_technical_issue: {is_technical_issue}, ai_explicitly_requested: {ai_explicitly_requested_ticket}")
        
        # Определяем, нужно ли создавать тикет:
        # 1. AI явно запросил тикет
        # 2. Нет релевантной информации (similarity < 0.2)
        # 3. Техническая проблема, требующая вмешательства
        if not needs_ticket:
            # Если AI не запросил явно, проверяем другие условия
            if max_similarity < 0.2:
                # Нет релевантной информации - создаем тикет
                needs_ticket = True
                print(f"[TICKET LOGIC] Setting needs_ticket=True because no relevant information (similarity < 0.2)")
            elif is_technical_issue:
                # Техническая проблема - создаем тикет
                needs_ticket = True
                print(f"[TICKET LOGIC] Setting needs_ticket=True because it's a technical issue")
        
        # Если нужно создать тикет, проверяем, не нужно ли его отменить
        if needs_ticket:
            # Если AI явно запросил тикет, всегда создаем (даже если есть релевантная информация)
            if ai_explicitly_requested_ticket:
                print(f"[TICKET LOGIC] Creating ticket because AI explicitly requested it")
                # Не отменяем создание тикета
            elif is_technical_issue:
                # Техническая проблема - всегда создаем тикет
                print(f"[TICKET LOGIC] Creating ticket because it's a technical issue")
            elif max_similarity < 0.2:
                # Нет релевантной информации - создаем тикет
                print(f"[TICKET LOGIC] Creating ticket because no relevant information (similarity < 0.2)")
            else:
                # Есть релевантная информация и это не техническая проблема - не создаем тикет
                print(f"[TICKET LOGIC] NOT creating ticket - have relevant info and not technical issue")
                needs_ticket = False
                confidence = max(0.2, max_similarity)
                answer = re.sub(r"Хорошо, ваш запрос зарегистрирован\. Наши специалисты свяжутся с вами\.", "", answer).strip()
        
        # Создаем тикет если нужно
        ticket_id_value = None
        categorization = None
        
        if needs_ticket:
            print(f"[TICKET CREATION] Starting ticket creation process...")
            categorization = categorize_ticket(message, conversation_history, client_type)
            
            conversation_text = "\n".join([
                f"{'Пользователь' if m['role'] == 'user' else 'Ассистент'}: {m['content']}"
                for m in conversation_history
            ])
            full_content = f"{conversation_text}\nПользователь: {message}"
            
            print(f"[TICKET CREATION] Ticket data: user_id={user_id}, client_type={client_type}, category={categorization['category']}, department={categorization['department']}, priority={categorization['priority']}")
            
            try:
                ticket_result = await create_ticket_from_chat(
                    user_id=user_id,
                    client_type=client_type,
                    language=language,
                    category=categorization["category"],
                    subcategory=categorization["subcategory"],
                    department=categorization["department"],
                    priority=categorization["priority"],
                    confidence=confidence,
                    content=full_content
                )
                
                ticket_id_value = ticket_result.get("id")
                print(f"[TICKET CREATION] Ticket created successfully: {ticket_id_value}")
                
                if "зарегистрирован" not in answer:
                    answer += "\n\nХорошо, ваш запрос зарегистрирован. Наши специалисты свяжутся с вами."
            except Exception as e:
                print(f"[TICKET CREATION] ERROR creating ticket: {e}")
                import traceback
                traceback.print_exc()
                # Не добавляем сообщение об ошибке пользователю, чтобы не пугать его
        
        # Формируем источники
        sources = [
            SourceInfo(
                content=chunk.get("content", ""),
                page=chunk.get("metadata", {}).get("page"),
                source_type=chunk.get("metadata", {}).get("source_type"),
                similarity=chunk.get("similarity")
            )
            for chunk in kazakhtelecom_chunks
        ]
        
        # Обновляем историю
        updated_history = request.conversation_history.copy()
        updated_history.append(PublicChatMessage(role="user", content=message, timestamp=datetime.now()))
        updated_history.append(PublicChatMessage(role="assistant", content=answer, timestamp=datetime.now()))
        
        # Вычисляем время ответа
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Сохраняем взаимодействие в БД для метрик
        try:
            interaction_data = {
                "user_id": user_id,
                "client_type": client_type,
                "message": message,
                "ai_response": answer,
                "conversation_history": [
                    {"role": msg.role, "content": msg.content, "timestamp": str(msg.timestamp) if msg.timestamp else None}
                    for msg in request.conversation_history
                ],
                "ticket_created": needs_ticket,
                "ticket_id": ticket_id_value,
                "confidence": confidence,
                "max_similarity": max_similarity,
                "is_technical_issue": is_technical_issue,
                "ai_explicitly_requested_ticket": ai_explicitly_requested_ticket,
                "category": categorization.get("category") if categorization and needs_ticket else None,
                "subcategory": categorization.get("subcategory") if categorization and needs_ticket else None,
                "department": categorization.get("department") if categorization and needs_ticket else None,
                "priority": categorization.get("priority") if categorization and needs_ticket else None,
                "language": language,
                "response_time_ms": response_time_ms,
                "sources": [
                    {
                        "content": s.content[:200] if s.content else "",  # Ограничиваем размер
                        "page": s.page,
                        "source_type": s.source_type,
                        "similarity": s.similarity
                    }
                    for s in sources[:5]  # Сохраняем только первые 5 источников
                ],
                "session_id": session_id
            }
            
            supabase = get_supabase_admin()
            supabase.table("chat_interactions").insert(interaction_data).execute()
            print(f"[CHAT_INTERACTION] Saved interaction: ticket_created={needs_ticket}, response_time={response_time_ms}ms, ticket_id={ticket_id_value}")
        except Exception as e:
            print(f"[CHAT_INTERACTION] Error saving interaction: {e}")
            import traceback
            traceback.print_exc()
            # Не прерываем выполнение, если не удалось сохранить
        
        # Всегда возвращаем ответ, независимо от успешности сохранения в БД
        return PublicChatResponse(
            response=answer,
            answer=answer,
            can_answer=confidence >= 0.2,
            needs_clarification=False,
            should_create_ticket=needs_ticket,
            sources=sources,
            confidence=confidence,
            ticketCreated=needs_ticket,
            conversation_history=updated_history
        )
            
    except Exception as e:
        print(f"Ошибка в public_chat: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке запроса: {str(e)}")


@router.post("/chat/create-ticket")
async def create_ticket_from_chat_endpoint(ticket_draft: Dict[str, Any]) -> Dict[str, Any]:
    """Создание тикета из драфта чата (для совместимости)"""
    try:
        from app.models.schemas import TicketSource
        
        conversation_history = ticket_draft.get("conversation_history", [])
        description = ticket_draft.get("description", "")
        
        if conversation_history:
            history_text = "\n\n=== История чата ===\n"
            for msg in conversation_history:
                role_name = "Клиент" if msg.get("role") == "user" else "ИИ-ассистент"
                content = msg.get("content", "")
                history_text += f"\n[{role_name}]: {content}\n"
            description = description + history_text
        
        ticket_data = {
            "source": TicketSource.CHAT.value,
            "subject": ticket_draft.get("subject", "Обращение через чат"),
            "text": description,
            "incoming_meta": {
                "language": ticket_draft.get("language", "ru"),
                "category": ticket_draft.get("category", "other"),
                "subcategory": ticket_draft.get("subcategory", "general"),
                "department": ticket_draft.get("department", "TechSupport"),
                "priority": ticket_draft.get("priority", "medium"),
                "summary": ticket_draft.get("summary", ""),
                "conversation_history": conversation_history,
                **ticket_draft.get("contact_info", {})
            }
        }
        
        result = await ticket_service.create_ticket(ticket_data)
        return {"success": True, "ticket_id": result.get("id"), "message": "Тикет успешно создан"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при создании тикета: {str(e)}")
