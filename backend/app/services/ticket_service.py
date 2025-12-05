"""
Ticket Service - Business logic for ticket management
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from app.core.database import get_supabase, get_supabase_admin
from app.core.config import settings
from app.models.schemas import TicketStatus, TicketPriority
from app.services.ai_service import ai_service
import uuid


class TicketService:
    """Service for ticket operations"""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.supabase_admin = get_supabase_admin()
    
    async def create_ticket(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new ticket"""
        ticket_id = str(uuid.uuid4())
        
        ticket_data = {
            "id": ticket_id,
            "client_id": data.get("client_id"),
            "source": data["source"],
            "source_meta": data.get("incoming_meta", {}),
            "subject": data["subject"],
            "description": data["text"],
            "status": TicketStatus.NEW.value,
            "priority": TicketPriority.MEDIUM.value,
            "auto_assigned": False,
            "auto_resolved": False,
            "need_on_site": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert ticket
        result = self.supabase_admin.table("tickets").insert(ticket_data).execute()
        
        if result.data:
            return result.data[0]
        raise Exception("Failed to create ticket")
    
    async def process_with_ai(self, ticket_id: str) -> Dict[str, Any]:
        """Process ticket with AI: classify, route, generate answer"""
        # Get ticket
        ticket_result = self.supabase_admin.table("tickets").select("*").eq("id", ticket_id).execute()
        
        if not ticket_result.data:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        ticket = ticket_result.data[0]
        
        # Classify
        classification = await ai_service.classify_ticket(
            ticket["description"],
            ticket.get("subject", "")
        )
        
        # Get department by name
        dept_result = self.supabase_admin.table("departments").select("id, sla_accept_minutes").eq("name", classification["department"]).execute()
        department_id = None
        sla_accept_minutes = settings.DEFAULT_SLA_ACCEPT_MINUTES
        
        if dept_result.data:
            department_id = dept_result.data[0]["id"]
            sla_accept_minutes = dept_result.data[0].get("sla_accept_minutes", settings.DEFAULT_SLA_ACCEPT_MINUTES)
        
        # Generate summary
        summary = await ai_service.generate_summary(ticket["description"], classification["language"])
        
        # RAG + Answer generation
        kb_snippets = await ai_service.retrieve_kb(ticket["description"], k=5)
        answer_result = await ai_service.generate_answer(
            ticket["description"],
            classification["language"],
            kb_snippets
        )
        
        # Determine auto-resolve
        auto_resolve = (
            classification["auto_resolve_candidate"] and
            classification["confidence"] > 0.7 and
            answer_result["confidence"] > 0.7 and
            not answer_result["need_on_site"]
        )
        
        # Calculate SLA deadlines
        now = datetime.utcnow()
        sla_accept_deadline = now + timedelta(minutes=sla_accept_minutes)
        sla_remote_deadline = sla_accept_deadline + timedelta(minutes=settings.DEFAULT_SLA_REMOTE_MINUTES)
        
        # Update ticket
        update_data = {
            "language": classification["language"],
            "category": classification["category"],
            "subcategory": classification["subcategory"],
            "department_id": department_id,
            "priority": classification["priority"],
            "summary": summary,
            "auto_assigned": True,
            "sla_accept_deadline": sla_accept_deadline.isoformat(),
            "sla_remote_deadline": sla_remote_deadline.isoformat(),
            "updated_at": now.isoformat()
        }
        
        if auto_resolve:
            update_data["status"] = TicketStatus.AUTO_RESOLVED.value
            update_data["auto_resolved"] = True
            update_data["closed_at"] = now.isoformat()
        
        if answer_result["need_on_site"]:
            update_data["need_on_site"] = True
        
        # Update ticket
        self.supabase_admin.table("tickets").update(update_data).eq("id", ticket_id).execute()
        
        # Log AI operation
        await self._log_ai_operation(ticket_id, classification, answer_result)
        
        return {
            "ticket_id": ticket_id,
            "language": classification["language"],
            "category": classification["category"],
            "subcategory": classification["subcategory"],
            "department_id": department_id,
            "priority": classification["priority"],
            "summary": summary,
            "auto_resolve": auto_resolve,
            "suggested_response": answer_result["answer"] if auto_resolve else None
        }
    
    async def _log_ai_operation(self, ticket_id: str, classification: Dict, answer_result: Dict):
        """Log AI operation for analytics"""
        log_data = {
            "id": str(uuid.uuid4()),
            "ticket_id": ticket_id,
            "prompt": f"Classification: {classification}",
            "ai_response": {
                "classification": classification,
                "answer": answer_result
            },
            "model": settings.OPENAI_MODEL,
            "created_at": datetime.utcnow().isoformat()
        }
        
        try:
            self.supabase_admin.table("ai_logs").insert(log_data).execute()
        except Exception as e:
            print(f"Failed to log AI operation: {e}")
    
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update ticket"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        
        result = self.supabase_admin.table("tickets").update(updates).eq("id", ticket_id).execute()
        
        if result.data:
            return result.data[0]
        raise ValueError(f"Ticket {ticket_id} not found")
    
    async def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get ticket by ID"""
        result = self.supabase_admin.table("tickets").select("*").eq("id", ticket_id).execute()
        return result.data[0] if result.data else None
    
    async def list_tickets(
        self,
        department_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List tickets with filters"""
        query = self.supabase_admin.table("tickets").select("*")
        
        if department_id:
            query = query.eq("department_id", department_id)
        if status:
            query = query.eq("status", status)
        
        query = query.order("created_at", desc=True).limit(limit).offset(offset)
        
        result = query.execute()
        return result.data if result.data else []


ticket_service = TicketService()

