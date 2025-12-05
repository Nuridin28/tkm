"""
Tickets API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.schemas import TicketUpdateRequest, TicketResponse
from app.services.ticket_service import ticket_service
from app.core.auth import get_current_user, require_role
from app.core.database import get_supabase_admin
from typing import Dict, Any, Optional, List
from datetime import datetime

router = APIRouter()


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> TicketResponse:
    """Get ticket by ID"""
    ticket = await ticket_service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return TicketResponse(**ticket)


@router.patch("/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    updates: TicketUpdateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update ticket (manual override)"""
    # Get current ticket to check for routing errors
    current_ticket = await ticket_service.get_ticket(ticket_id)
    if not current_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    update_dict = updates.model_dump(exclude_unset=True)
    
    # Convert enums to strings
    if "status" in update_dict:
        update_dict["status"] = update_dict["status"].value
    if "priority" in update_dict:
        update_dict["priority"] = update_dict["priority"].value
    
    # Log routing error if department changed
    if "department_id" in update_dict and update_dict["department_id"] != current_ticket.get("department_id"):
        await ticket_service._log_routing_error(
            ticket_id=ticket_id,
            initial_department_id=current_ticket.get("department_id"),
            correct_department_id=update_dict["department_id"],
            routed_by=user.get("id"),
            error_type="wrong_department"
        )
    
    ticket = await ticket_service.update_ticket(ticket_id, update_dict)
    return ticket


@router.post("/{ticket_id}/accept")
async def accept_ticket(
    ticket_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Accept ticket (agent action)"""
    # Get ticket to calculate response time
    ticket = await ticket_service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    now = datetime.utcnow()
    created_at = datetime.fromisoformat(ticket["created_at"].replace('Z', '+00:00'))
    response_time_seconds = int((now - created_at).total_seconds())
    
    updates = {
        "status": "accepted",
        "first_response_at": now.isoformat()
    }
    ticket = await ticket_service.update_ticket(ticket_id, updates)
    
    # Log response time
    await ticket_service._log_response_time(ticket_id, now, response_time_seconds, "human")
    
    return ticket


@router.post("/{ticket_id}/complete_remote")
async def complete_remote(
    ticket_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Mark ticket as resolved remotely"""
    updates = {"status": "resolved"}
    ticket = await ticket_service.update_ticket(ticket_id, updates)
    return ticket


@router.post("/{ticket_id}/request_on_site")
async def request_on_site(
    ticket_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Request on-site visit"""
    updates = {"need_on_site": True, "status": "on_site"}
    ticket = await ticket_service.update_ticket(ticket_id, updates)
    return ticket


@router.get("/{ticket_id}/messages")
async def get_messages(
    ticket_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get messages for a ticket"""
    supabase = get_supabase_admin()
    result = supabase.table("messages").select("*").eq("ticket_id", ticket_id).order("created_at").execute()
    return result.data if result.data else []


@router.get("")
async def list_tickets(
    department_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List tickets with filters"""
    tickets = await ticket_service.list_tickets(
        department_id=department_id,
        status=status,
        limit=limit,
        offset=offset
    )
    return tickets


@router.delete("/{ticket_id}")
async def delete_ticket(
    ticket_id: str,
    user: Dict[str, Any] = Depends(require_role(["admin", "supervisor"]))
) -> Dict[str, Any]:
    """Delete ticket (admin only)"""
    supabase = get_supabase_admin()
    try:
        # Удалить связанные сообщения
        supabase.table("messages").delete().eq("ticket_id", ticket_id).execute()
        # Удалить тикет
        result = supabase.table("tickets").delete().eq("id", ticket_id).execute()
        return {"success": True, "message": "Ticket deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to delete ticket: {str(e)}")


@router.post("/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: str,
    assigned_to: Optional[str] = None,
    department_id: Optional[str] = None,
    user: Dict[str, Any] = Depends(require_role(["admin", "supervisor"]))
) -> Dict[str, Any]:
    """Assign ticket to user or department (admin only)"""
    updates = {}
    if assigned_to:
        updates["assigned_to"] = assigned_to
    if department_id:
        updates["department_id"] = department_id
    if updates:
        updates["status"] = "accepted"
        ticket = await ticket_service.update_ticket(ticket_id, updates)
        return ticket
    raise HTTPException(status_code=400, detail="No assignment data provided")
