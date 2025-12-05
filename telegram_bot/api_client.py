"""
API Client for communicating with backend
"""
import httpx
from typing import Dict, Any, Optional
from config import settings
from models import TicketRequest
import os


class APIClient:
    """Client for backend API"""
    
    def __init__(self):
        self.base_url = settings.API_URL
        self.timeout = 30.0
    
    async def analyze_message(self, message: str, contact_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze message using RAG/AI service
        Returns: {
            "can_answer": bool,
            "answer": Optional[str],
            "category": Optional[str],
            "priority": Optional[str],
            "department": Optional[str],
            "subject": Optional[str]
        }
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Используем Telegram endpoint для анализа
                response = await client.post(
                    f"{self.base_url}/api/telegram/analyze",
                    json={
                        "text": message,
                        "contact_info": contact_info or {}
                    },
                    headers={
                        "X-Telegram-API-Key": settings.TELEGRAM_BOT_API_KEY or 'dev_key'
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error analyzing message: {e}")
            return {
                "can_answer": False,
                "answer": None,
                "category": None,
                "priority": "medium",
                "department": None,
                "subject": message[:50] + "..." if len(message) > 50 else message
            }
    
    async def create_ticket(self, ticket_request: TicketRequest) -> Dict[str, Any]:
        """Create ticket via backend API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Создаем тикет через Telegram endpoint
                response = await client.post(
                    f"{self.base_url}/api/telegram/create-ticket",
                    json={
                        "source": "telegram",
                        "subject": ticket_request.subject,
                        "text": ticket_request.description,
                        "contact_info": ticket_request.contact_info.model_dump(),
                        "telegram_user_id": ticket_request.telegram_user_id,
                        "telegram_chat_id": ticket_request.telegram_chat_id,
                        "telegram_username": ticket_request.telegram_username
                    },
                    headers={
                        "X-Telegram-API-Key": settings.TELEGRAM_BOT_API_KEY or 'dev_key'
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error creating ticket: {e}")
            raise

