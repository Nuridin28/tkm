import httpx
from typing import Dict, Any, Optional, List
from config import settings
from models import TicketRequest
from datetime import datetime
import os


class APIClient:

    def __init__(self):
        self.base_url = settings.API_URL
        self.timeout = 30.0

    async def analyze_message(self, message: str, contact_info: Optional[Dict[str, Any]] = None, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                formatted_history = []
                if conversation_history:
                    for msg in conversation_history:
                        formatted_history.append({
                            "role": msg.get("role", "user"),
                            "content": msg.get("content", ""),
                            "timestamp": msg.get("timestamp", datetime.now().isoformat())
                        })

                chat_contact_info = {}
                if contact_info:
                    if "phone" in contact_info:
                        chat_contact_info["phone"] = str(contact_info["phone"])
                    if "email" in contact_info:
                        chat_contact_info["email"] = str(contact_info["email"])
                    if "full_name" in contact_info:
                        chat_contact_info["name"] = str(contact_info["full_name"])

                response = await client.post(
                    f"{self.base_url}/api/public/chat",
                    json={
                        "message": message,
                        "conversation_history": formatted_history,
                        "contact_info": chat_contact_info
                    }
                )
                response.raise_for_status()
                result = response.json()

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
                    "conversation_history": result.get("conversation_history", [])
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
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if ticket_draft:
                    response = await client.post(
                        f"{self.base_url}/api/public/chat/create-ticket",
                        json=ticket_draft
                    )
                else:
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
                            "email": contact_info.get("email"),
                            "name": contact_info.get("full_name", ""),
                            "telegram_user_id": ticket_request.telegram_user_id,
                            "telegram_chat_id": ticket_request.telegram_chat_id,
                            "telegram_username": ticket_request.telegram_username
                        },
                        "conversation_history": []
                    }
                    response = await client.post(
                        f"{self.base_url}/api/public/chat/create-ticket",
                        json=ticket_draft_data
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

