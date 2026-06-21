from datetime import date

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.models import BodyMetric
from backend.app.schemas import BodyMetricRequest


class BodyMetricService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, request: BodyMetricRequest) -> BodyMetric:
        measurements = dict(request.measurements or {})
        metric = BodyMetric(
            user_id=user_id,
            measured_on=request.measured_on or date.today(),
            weight_kg=request.weight_kg,
            body_fat_percent=request.body_fat_percent,
            waist_cm=measurements.get("waist_cm"),
            measurements_json=measurements,
            source=request.source.strip(),
            note=request.note,
        )
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def recent(self, user_id: int, limit: int = 10) -> list[BodyMetric]:
        bounded_limit = max(1, min(limit, 50))
        return list(
            self.db.scalars(
                select(BodyMetric)
                .where(BodyMetric.user_id == user_id)
                .order_by(desc(BodyMetric.measured_on), desc(BodyMetric.id))
                .limit(bounded_limit)
            ).all()
        )

    def latest(self, user_id: int) -> BodyMetric | None:
        return self.db.scalar(
            select(BodyMetric)
            .where(BodyMetric.user_id == user_id)
            .order_by(desc(BodyMetric.measured_on), desc(BodyMetric.id))
        )

    @staticmethod
    def serialize(metric: BodyMetric) -> dict:
        measurements = dict(metric.measurements_json or {})
        if metric.waist_cm is not None and "waist_cm" not in measurements:
            measurements["waist_cm"] = metric.waist_cm
        return {
            "id": metric.id,
            "measured_on": metric.measured_on.isoformat(),
            "weight_kg": metric.weight_kg,
            "body_fat_percent": metric.body_fat_percent,
            "measurements": measurements,
            "source": metric.source,
            "note": metric.note,
        }
