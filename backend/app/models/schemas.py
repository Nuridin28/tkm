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
    WHATSAPP = "whatsapp"


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


class ClassificationAccuracy(BaseModel):
    total_classifications: int
    correct_classifications: int
    accuracy_percentage: float
    by_category: Dict[str, float]
    by_department: Dict[str, float]


class AutoResolveStats(BaseModel):
    total_auto_resolved: int
    total_tickets: int
    auto_resolve_rate: float
    avg_confidence: float
    by_category: Dict[str, int]


class ResponseTimeStats(BaseModel):
    avg_response_time_seconds: float
    median_response_time_seconds: float
    p95_response_time_seconds: float
    by_source: Dict[str, float]
    by_department: Dict[str, float]


class RoutingErrorStats(BaseModel):
    total_routing_errors: int
    error_rate: float
    by_error_type: Dict[str, int]
    by_department: Dict[str, int]
    by_category: Optional[Dict[str, int]] = {}


class MonitoringMetrics(BaseModel):
    classification_accuracy: ClassificationAccuracy
    auto_resolve_stats: AutoResolveStats
    response_time_stats: ResponseTimeStats
    routing_error_stats: RoutingErrorStats
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


class PublicChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None


class PublicChatRequest(BaseModel):
    message: str
    conversation_history: List[PublicChatMessage] = []
    contact_info: Optional[Dict[str, str]] = None


class SourceInfo(BaseModel):
    content: str
    page: Optional[int] = None
    source_type: Optional[str] = None
    similarity: Optional[float] = None


class PublicChatResponse(BaseModel):
    response: str
    answer: Optional[str] = None
    can_answer: bool = True
    needs_clarification: bool = False
    should_create_ticket: bool = False
    ticket_draft: Optional[Dict[str, Any]] = None
    conversation_history: List[PublicChatMessage] = []
    sources: Optional[List[SourceInfo]] = []
    confidence: Optional[float] = None
    ticketCreated: Optional[bool] = False
    requiresClientType: Optional[bool] = False

