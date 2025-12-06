import json
from typing import Dict, Any, Optional, List
from openai import OpenAI
from app.core.config import settings
from app.core.database import get_supabase
from langdetect import detect, LangDetectException

_client = None

def get_openai_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


class AIService:

    def __init__(self):
        self.model = settings.OPENAI_MODEL
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL

    def detect_language(self, text: str) -> str:
        try:
            lang = detect(text)
            if lang in ['ru', 'kk', 'kz']:
                return 'ru' if lang == 'ru' else 'kz'
            return 'ru'
        except LangDetectException:
            return 'ru'

    def get_embedding(self, text: str) -> List[float]:
        client = get_openai_client()
        response = client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding

    async def classify_ticket(self, ticket_text: str, subject: str = "") -> Dict[str, Any]:
        full_text = f"Subject: {subject}\n\nDescription: {ticket_text}"

        system_prompt = """Ты — классификатор тикетов для телеком-компании. 
Вход — текст обращения клиента. Вывод — строго валидный JSON с полями:
- language: "ru" или "kz"
- category: одна из ("network", "telephony", "tv", "billing", "equipment", "other")
- subcategory: более конкретная категория (например "vpn_access", "internet_speed", "payment_issue")
- department: одна из ("TechSupport", "Network", "Sales", "Billing", "LocalOffice")
- priority: одна из ("critical", "high", "medium", "low")
- auto_resolve_candidate: true/false (true если проблема может быть решена автоматически)
- confidence: число от 0 до 1

Если не уверен в решении — auto_resolve_candidate=false, confidence < 0.7.
Выводи ТОЛЬКО JSON, без дополнительного текста."""

        user_prompt = full_text

        try:
            client = get_openai_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            return {
                "language": result.get("language", "ru"),
                "category": result.get("category", "other"),
                "subcategory": result.get("subcategory", "general"),
                "department": result.get("department", "TechSupport"),
                "priority": result.get("priority", "medium"),
                "auto_resolve_candidate": result.get("auto_resolve_candidate", False),
                "confidence": float(result.get("confidence", 0.5))
            }
        except Exception as e:
            return {
                "language": self.detect_language(ticket_text),
                "category": "other",
                "subcategory": "general",
                "department": "TechSupport",
                "priority": "medium",
                "auto_resolve_candidate": False,
                "confidence": 0.0
            }

    async def generate_ticket_summary(self, conversation_history: List[Dict[str, Any]], user_message: str) -> str:
        try:
            history_text = ""
            for msg in conversation_history[-5:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    history_text += f"Клиент: {content}\n"

            history_text += f"Клиент: {user_message}\n"

            system_prompt = """Ты — помощник для создания краткого описания проблемы клиента для тикета техподдержки.

На основе истории разговора с клиентом создай краткое, но информативное описание проблемы:
- Укажи суть проблемы (что не работает, что нужно)
- Укажи важные детали (если есть)
- НЕ включай ответы ассистента, только проблему клиента
- Длина: 2-4 предложения
- Пиши от лица клиента или в нейтральном тоне

Примеры:
"Клиент не может зарегистрироваться в личном кабинете. Нужна помощь с получением регистрационных кодов."
"У клиента не работает интернет. Требуется диагностика проблемы."
"Клиент хочет узнать, как приостановить услуги связи на время."

Отвечай ТОЛЬКО описанием проблемы, без дополнительных комментариев."""

            client = get_openai_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": history_text}
                ],
                temperature=0.3,
                max_tokens=200
            )

            summary = response.choices[0].message.content.strip()
            return summary

        except Exception as e:
            print(f"Error generating ticket summary: {e}")
            return user_message[:200] + ("..." if len(user_message) > 200 else "")

    async def retrieve_kb(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        supabase = get_supabase()

        query_embedding = self.get_embedding(query)

        try:
            results = supabase.rpc(
                'match_embeddings',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': 0.7,
                    'match_count': k
                }
            ).execute()

            return results.data if results.data else []
        except Exception as e:
            print(f"RAG retrieval error: {e}")
            return []

    async def generate_answer(
        self,
        ticket_text: str,
        language: str,
        kb_snippets: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        snippets_text = ""
        if kb_snippets:
            snippets_text = "\n\nСправочные материалы:\n"
            for snippet in kb_snippets[:3]:
                snippets_text += f"- {snippet.get('text_excerpt', snippet.get('content', ''))}\n"

        system_prompt = f"""Ты — ассистент техподдержки телеком-компании.
Используй предоставленные справочные материалы для формирования ответа.
Сформируй ответ клиенту на языке {language} (RU или KZ), кратко (2-4 предложения), 
с указанием следующих шагов. Если решение найдено в материалах — включи шаги.
Если не найдено — предложи диагностику и пометь need_on_site=true.

Выведи JSON с полями:
- answer: текст ответа клиенту
- resolution_steps: массив шагов решения (если есть)
- need_on_site: true/false
- confidence: уверенность в решении (0-1)"""

        user_prompt = f"{snippets_text}\n\nОбращение клиента:\n{ticket_text}"

        try:
            client = get_openai_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return {
                "answer": result.get("answer", ""),
                "resolution_steps": result.get("resolution_steps", []),
                "need_on_site": result.get("need_on_site", False),
                "confidence": float(result.get("confidence", 0.5))
            }
        except Exception as e:
            return {
                "answer": f"Спасибо за обращение. Мы рассмотрим вашу заявку в ближайшее время.",
                "resolution_steps": [],
                "need_on_site": False,
                "confidence": 0.0
            }

    async def generate_summary(self, ticket_text: str, language: str = "ru") -> str:
        prompt = f"Создай краткое резюме (1-3 предложения) на языке {language}:\n\n{ticket_text}"

        try:
            client = get_openai_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return ticket_text[:200] + "..." if len(ticket_text) > 200 else ticket_text


ai_service = AIService()

