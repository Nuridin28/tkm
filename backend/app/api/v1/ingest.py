from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import IngestRequest
from app.services.ticket_service import ticket_service
from app.core.auth import get_current_user
from typing import Dict, Any

router = APIRouter()


@router.post("")
async def ingest_ticket(
    request: IngestRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    try:
        ticket_data = {
            "source": request.source.value,
            "client_id": request.client_id,
            "subject": request.subject,
            "text": request.text,
            "incoming_meta": request.incoming_meta
        }

        ticket = await ticket_service.create_ticket(ticket_data)

        ai_result = await ticket_service.process_with_ai(ticket["id"])

        return {
            "ticket_id": ticket["id"],
            "status": "created",
            "ai_processing": ai_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

