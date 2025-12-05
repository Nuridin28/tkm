"""
Pydantic schemas for request/response models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TicketSource(str, Enum):
    PORTAL = "portal"
    CHAT = "chat"
    EMAIL = "email"
    PHONE = "phone"
    CALL_AGENT = "call_agent"
    TELEGRAM = "telegram"


class TicketStatus(str, Enum):
    NEW = "new"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    AUTO_RESOLVED = "auto_resolved"
    ESCALATED = "escalated"
    ON_SITE = "on_site"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    DEPARTMENT_USER = "department_user"
    SUPERVISOR = "supervisor"
    ENGINEER = "engineer"
    CALL_AGENT = "call_agent"
    MANAGER = "manager"


# Request schemas
class IngestRequest(BaseModel):
    source: TicketSource
    client_id: Optional[str] = None
    subject: str
    text: str
    attachments: List[Dict[str, Any]] = []
    incoming_meta: Dict[str, Any] = {}


class AIProcessRequest(BaseModel):
    ticket_id: str


class TicketUpdateRequest(BaseModel):
    department_id: Optional[str] = None
    assigned_to: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    need_on_site: Optional[bool] = None
    engineer_id: Optional[str] = None


class AISearchRequest(BaseModel):
    query: str
    k: int = 5


# Response schemas
class AIProcessResponse(BaseModel):
    ticket_id: str
    language: str
    category: str
    subcategory: str
    department_id: str
    priority: TicketPriority
    summary: str
    auto_resolve: bool
    suggested_response: Optional[str] = None


class TicketResponse(BaseModel):
    id: str
    client_id: Optional[str]
    source: TicketSource
    subject: str
    description: str
    language: Optional[str]
    summary: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    department_id: Optional[str]
    assigned_to: Optional[str]
    priority: TicketPriority
    status: TicketStatus
    auto_assigned: bool
    auto_resolved: bool
    need_on_site: bool
    local_office_id: Optional[str]
    engineer_id: Optional[str]
    sla_accept_deadline: Optional[datetime]
    sla_remote_deadline: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]


class MessageResponse(BaseModel):
    id: str
    ticket_id: str
    sender_type: str
    sender_id: Optional[str]
    text: str
    attachments: Optional[Dict[str, Any]]
    created_at: datetime


class MetricsResponse(BaseModel):
    total_tickets: int
    auto_resolve_rate: float
    sla_compliance: float
    classification_accuracy: Optional[float]
    avg_response_time: Optional[float]
    period_from: datetime
    period_to: datetime


class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    role: UserRole
    department_id: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    created_at: Optional[str] = None


class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None


class DepartmentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

