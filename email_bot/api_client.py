"""
API Client for communicating with backend
"""
import httpx
from typing import Dict, Any, Optional, List
from config import settings
from models import TicketRequest
from datetime import datetime
import os


class APIClient:
    """Client for backend API"""
    
    def __init__(self):
        self.base_url = settings.API_URL
        self.timeout = 30.0
        self.api_key = settings.EMAIL_BOT_API_KEY
    
    async def analyze_message(self, message: str, contact_info: Optional[Dict[str, Any]] = None, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Analyze message using RAG/AI service via public chat API
        Returns: {
            "can_answer": bool,
            "answer": Optional[str],
            "response": Optional[str],
            "category": Optional[str],
            "priority": Optional[str],
            "department": Optional[str],
            "subject": Optional[str],
            "confidence": Optional[float],
            "ticketCreated": Optional[bool],
            "ticket_draft": Optional[Dict]
        }
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Используем основной public chat API endpoint
                # Формируем conversation_history в формате PublicChatMessage
                formatted_history = []
                if conversation_history:
                    for msg in conversation_history:
                        formatted_history.append({
                            "role": msg.get("role", "user"),
                            "content": msg.get("content", ""),
                            "timestamp": msg.get("timestamp", datetime.now().isoformat())
                        })
                
                # Формируем contact_info
                chat_contact_info = {}
                if contact_info:
                    if "phone" in contact_info:
                        chat_contact_info["phone"] = str(contact_info["phone"])
                    if "email" in contact_info:
                        chat_contact_info["email"] = str(contact_info["email"])
                    if "full_name" in contact_info or "name" in contact_info:
                        chat_contact_info["name"] = str(contact_info.get("full_name") or contact_info.get("name", ""))
                
                headers = {}
                if self.api_key:
                    headers["X-Email-Bot-API-Key"] = self.api_key
                
                response = await client.post(
                    f"{self.base_url}/api/public/chat",
                    json={
                        "message": message,
                        "conversation_history": formatted_history,
                        "contact_info": chat_contact_info
                    },
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
                
                # Адаптируем ответ под формат, ожидаемый ботом
                return {
                    "can_answer": result.get("can_answer", True) and not result.get("ticketCreated", False),
                    "answer": result.get("response") or result.get("answer"),
                    "response": result.get("response"),
                    "category": result.get("ticket_draft", {}).get("category") if result.get("ticket_draft") else None,
                    "priority": result.get("ticket_draft", {}).get("priority", "medium") if result.get("ticket_draft") else "medium",
                    "department": result.get("ticket_draft", {}).get("department") if result.get("ticket_draft") else None,
                    "subject": message[:50] + "..." if len(message) > 50 else message,
                    "confidence": result.get("confidence", 0.0),
                    "ticketCreated": result.get("ticketCreated", False),
                    "ticket_draft": result.get("ticket_draft"),
                    "conversation_history": result.get("conversation_history", [])  # Возвращаем обновленную историю
                }
        except Exception as e:
            print(f"Error analyzing message: {e}")
            import traceback
            traceback.print_exc()
            return {
                "can_answer": False,
                "answer": None,
                "response": None,
                "category": None,
                "priority": "medium",
                "department": None,
                "subject": message[:50] + "..." if len(message) > 50 else message,
                "confidence": 0.0,
                "ticketCreated": False
            }
    
    async def create_ticket(self, ticket_request: TicketRequest, ticket_draft: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create ticket via backend API using public chat endpoint"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {}
                if self.api_key:
                    headers["X-Email-Bot-API-Key"] = self.api_key
                
                # Если есть ticket_draft из предыдущего запроса, используем его
                if ticket_draft:
                    response = await client.post(
                        f"{self.base_url}/api/public/chat/create-ticket",
                        json=ticket_draft,
                        headers=headers
                    )
                else:
                    # Создаем ticket_draft на основе ticket_request
                    contact_info = ticket_request.contact_info.model_dump() if ticket_request.contact_info else {}
                    ticket_draft_data = {
                        "subject": ticket_request.subject,
                        "description": ticket_request.description,
                        "language": "ru",
                        "category": "other",
                        "subcategory": "general",
                        "department": "TechSupport",
                        "priority": "medium",
                        "contact_info": {
                            "phone": contact_info.get("phone", ""),
                            "email": contact_info.get("email") or ticket_request.email_address,
                            "name": contact_info.get("full_name", ""),
                            "email_address": ticket_request.email_address,
                            "email_message_id": ticket_request.email_message_id
                        },
                        "conversation_history": []
                    }
                    response = await client.post(
                        f"{self.base_url}/api/public/chat/create-ticket",
                        json=ticket_draft_data,
                        headers=headers
                    )
                
                response.raise_for_status()
                result = response.json()
                return {
                    "ticket_id": result.get("ticket_id"),
                    "status": "created",
                    "priority": ticket_draft.get("priority", "medium") if ticket_draft else "medium",
                    "department": ticket_draft.get("department", "TechSupport") if ticket_draft else "TechSupport"
                }
        except Exception as e:
            print(f"Error creating ticket: {e}")
            import traceback
            traceback.print_exc()
            raise

