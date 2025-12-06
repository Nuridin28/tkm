from typing import Optional, Literal, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from email.message import EmailMessage


class UserType(str, Enum):
    INDIVIDUAL = "individual"
    LEGAL = "legal"


class ContactInfo(BaseModel):
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    user_type: UserType = Field(default=UserType.INDIVIDUAL, description="Individual or Legal entity")

    company_name: Optional[str] = Field(None, description="Company name (for legal entities)")
    inn: Optional[str] = Field(None, description="INN/Tax ID (for legal entities)")


class EmailSession(BaseModel):
    email_address: str
    contact_info: Optional[ContactInfo] = None
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation history for RAG")
    ticket_draft: Optional[Dict[str, Any]] = Field(default=None, description="Draft ticket data from chat API")
    last_message_id: Optional[str] = None


class TicketRequest(BaseModel):
    source: Literal["email"] = "email"
    subject: str
    description: str
    contact_info: ContactInfo
    email_address: str
    email_message_id: Optional[str] = None

