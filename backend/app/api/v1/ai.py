from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import AIProcessRequest, AIProcessResponse, AISearchRequest
from app.services.ticket_service import ticket_service
from app.services.ai_service import ai_service
from app.core.auth import get_current_user
from typing import Dict, Any, List

router = APIRouter()


@router.post("/process", response_model=AIProcessResponse)
async def process_ticket_with_ai(
    request: AIProcessRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> AIProcessResponse:
    try:
        result = await ticket_service.process_with_ai(request.ticket_id)
        return AIProcessResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_kb(
    request: AISearchRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    try:
        results = await ai_service.retrieve_kb(request.query, k=request.k)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

