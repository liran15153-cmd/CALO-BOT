from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.auth import get_current_user
from backend.app.db import get_db
from backend.app.models import User
from backend.app.schemas import PendingActionResolveRequest
from backend.app.services.pending_action_service import PendingActionService, WORKOUT_PLAN_REPLACEMENT_ACTION


router = APIRouter(prefix="/api/pending-actions", tags=["pending-actions"])


@router.get("/current")
def get_current_pending_action(
    action_type: str = WORKOUT_PLAN_REPLACEMENT_ACTION,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    service = PendingActionService(db)
    action = service.current(user_id=user.id, action_type=action_type)
    if action is None:
        raise HTTPException(status_code=404, detail="No pending action")
    return service.serialize(action, include_candidate_plan=True)


@router.post("/{action_id}/resolve")
def resolve_pending_action(
    action_id: int,
    payload: PendingActionResolveRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        return PendingActionService(db).resolve(user_id=user.id, action_id=action_id, decision=payload.decision)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
