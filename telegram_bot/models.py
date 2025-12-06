from typing import Optional, Literal, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class UserType(str, Enum):
    INDIVIDUAL = "individual"
    LEGAL = "legal"


class ContactInfo(BaseModel):
    phone: str = Field(..., description="Phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")
    full_name: str = Field(..., description="Full name")
    user_type: UserType = Field(..., description="Individual or Legal entity")

    company_name: Optional[str] = Field(None, description="Company name (for legal entities)")
    inn: Optional[str] = Field(None, description="INN/Tax ID (for legal entities)")

    passport: Optional[str] = Field(None, description="Passport number (for individuals)")


class UserSession(BaseModel):
    user_id: int
    chat_id: int
    username: Optional[str] = None
    contact_info: Optional[ContactInfo] = None
    current_message: Optional[str] = None
    waiting_for: Optional[str] = None
    language: str = "ru"
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation history for RAG")
    ticket_draft: Optional[Dict[str, Any]] = Field(default=None, description="Draft ticket data from chat API")


class TicketRequest(BaseModel):
    source: Literal["telegram"] = "telegram"
    subject: str
    description: str
    contact_info: ContactInfo
    telegram_user_id: int
    telegram_chat_id: int
    telegram_username: Optional[str] = None

