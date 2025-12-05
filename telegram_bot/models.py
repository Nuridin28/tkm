"""
Data models for Telegram Bot
"""
from typing import Optional, Literal, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class UserType(str, Enum):
    """Type of user"""
    INDIVIDUAL = "individual"  # Физическое лицо
    LEGAL = "legal"  # Юридическое лицо


class ContactInfo(BaseModel):
    """Contact information"""
    phone: str = Field(..., description="Phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")
    full_name: str = Field(..., description="Full name")
    user_type: UserType = Field(..., description="Individual or Legal entity")
    
    # For legal entities
    company_name: Optional[str] = Field(None, description="Company name (for legal entities)")
    inn: Optional[str] = Field(None, description="INN/Tax ID (for legal entities)")
    
    # For individuals
    passport: Optional[str] = Field(None, description="Passport number (for individuals)")


class UserSession(BaseModel):
    """User session state"""
    user_id: int
    chat_id: int
    username: Optional[str] = None
    contact_info: Optional[ContactInfo] = None
    current_message: Optional[str] = None
    waiting_for: Optional[str] = None  # "phone", "email", "name", "type", "message", etc.
    language: str = "ru"
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation history for RAG")
    ticket_draft: Optional[Dict[str, Any]] = Field(default=None, description="Draft ticket data from chat API")


class TicketRequest(BaseModel):
    """Ticket creation request"""
    source: Literal["telegram"] = "telegram"
    subject: str
    description: str
    contact_info: ContactInfo
    telegram_user_id: int
    telegram_chat_id: int
    telegram_username: Optional[str] = None

