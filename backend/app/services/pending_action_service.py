from datetime import UTC, datetime
from typing import Any, Literal

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.models import PendingAction, WorkoutPlan
from backend.app.services.workout_service import WorkoutService


WORKOUT_PLAN_REPLACEMENT_ACTION = "activate_workout_plan"
WORKOUT_PLAN_SUBJECT = "workout_plan"
PendingDecision = Literal["confirm", "decline"]


class PendingActionService:
    def __init__(self, db: Session):
        self.db = db

    def current(self, *, user_id: int, action_type: str = WORKOUT_PLAN_REPLACEMENT_ACTION) -> PendingAction | None:
        return self.db.scalar(
            select(PendingAction)
            .where(
                PendingAction.user_id == user_id,
                PendingAction.action_type == action_type,
                PendingAction.status == "pending",
            )
            .order_by(desc(PendingAction.created_at), desc(PendingAction.id))
        )

    def create_workout_plan_replacement(
        self,
        *,
        user_id: int,
        candidate_plan_id: int,
        current_plan_id: int,
        session_id: int | None = None,
        created_from_message_id: int | None = None,
    ) -> PendingAction:
        self._replace_open_workout_plan_actions(user_id=user_id, next_candidate_plan_id=candidate_plan_id)
        action = PendingAction(
            user_id=user_id,
            session_id=session_id,
            action_type=WORKOUT_PLAN_REPLACEMENT_ACTION,
            status="pending",
            subject_type=WORKOUT_PLAN_SUBJECT,
            subject_id=candidate_plan_id,
            payload_json={"current_plan_id": current_plan_id, "delete_previous": True},
            created_from_message_id=created_from_message_id,
        )
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action

    def resolve(self, *, user_id: int, action_id: int, decision: PendingDecision, resolved_by_message_id: int | None = None) -> dict[str, Any]:
        action = self.db.get(PendingAction, action_id)
        if action is None or action.user_id != user_id:
            raise ValueError("הפעולה הממתינה לא נמצאה")
        if action.status != "pending":
            raise RuntimeError("הפעולה הממתינה כבר לא פתוחה")
        if action.action_type != WORKOUT_PLAN_REPLACEMENT_ACTION or action.subject_type != WORKOUT_PLAN_SUBJECT:
            raise RuntimeError("סוג הפעולה הממתינה אינו נתמך")

        candidate = self.db.get(WorkoutPlan, action.subject_id)
        if candidate is None or candidate.user_id != user_id:
            self._mark(action, status="cancelled", resolution="candidate_missing", resolved_by_message_id=resolved_by_message_id)
            return {
                "pending_action": self.serialize(action),
                "workout_plan": self._current_plan_payload(user_id=user_id),
                "message": "התוכנית החדשה כבר לא זמינה. התוכנית הפעילה נשארת ללא שינוי.",
            }

        workout_service = WorkoutService(self.db)
        if decision == "confirm":
            plan = workout_service.activate_plan(user_id=user_id, plan_id=action.subject_id, delete_previous=True)
            self._mark(action, status="resolved", resolution="confirmed", resolved_by_message_id=resolved_by_message_id)
            return {
                "pending_action": self.serialize(action),
                "workout_plan": workout_service.serialize_plan_with_rows(plan),
                "message": "התוכנית החדשה פעילה עכשיו.",
            }

        workout_service.delete_plan(user_id=user_id, plan_id=action.subject_id)
        self._mark(action, status="resolved", resolution="declined", resolved_by_message_id=resolved_by_message_id)
        return {
            "pending_action": self.serialize(action),
            "workout_plan": self._current_plan_payload(user_id=user_id),
            "message": "התוכנית הפעילה נשארת.",
        }

    def serialize(self, action: PendingAction, *, include_candidate_plan: bool = False) -> dict[str, Any]:
        payload = {
            "id": action.id,
            "user_id": action.user_id,
            "session_id": action.session_id,
            "action_type": action.action_type,
            "status": action.status,
            "subject_type": action.subject_type,
            "subject_id": action.subject_id,
            "payload": action.payload_json or {},
            "resolution": action.resolution,
            "created_from_message_id": action.created_from_message_id,
            "resolved_by_message_id": action.resolved_by_message_id,
            "created_at": action.created_at.isoformat() if action.created_at else None,
            "resolved_at": action.resolved_at.isoformat() if action.resolved_at else None,
        }
        if include_candidate_plan:
            candidate = self.db.get(WorkoutPlan, action.subject_id)
            payload["candidate_plan"] = (
                WorkoutService(self.db).serialize_plan_with_rows(candidate)
                if candidate is not None and candidate.user_id == action.user_id
                else None
            )
        return payload

    def _replace_open_workout_plan_actions(self, *, user_id: int, next_candidate_plan_id: int) -> None:
        open_actions = self.db.scalars(
            select(PendingAction).where(
                PendingAction.user_id == user_id,
                PendingAction.action_type == WORKOUT_PLAN_REPLACEMENT_ACTION,
                PendingAction.status == "pending",
            )
        ).all()
        workout_service = WorkoutService(self.db)
        for action in open_actions:
            if action.subject_id == next_candidate_plan_id:
                continue
            self._mark(action, status="cancelled", resolution="replaced", commit=False)
            candidate = self.db.get(WorkoutPlan, action.subject_id)
            if candidate is not None and candidate.user_id == user_id and not candidate.is_current:
                workout_service.delete_plan(user_id=user_id, plan_id=candidate.id)
        self.db.flush()

    def _mark(
        self,
        action: PendingAction,
        *,
        status: str,
        resolution: str,
        resolved_by_message_id: int | None = None,
        commit: bool = True,
    ) -> None:
        action.status = status
        action.resolution = resolution
        action.resolved_by_message_id = resolved_by_message_id
        action.resolved_at = datetime.now(UTC)
        if commit:
            self.db.commit()
            self.db.refresh(action)

    def _current_plan_payload(self, *, user_id: int) -> dict[str, Any] | None:
        plan = WorkoutService(self.db).current_plan(user_id=user_id)
        return WorkoutService(self.db).serialize_plan_with_rows(plan) if plan is not None else None
