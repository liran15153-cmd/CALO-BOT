from datetime import date
import json
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.models import Meal, MealImageAnalysis, MealItem
from backend.app.schemas import MealTextRequest
from backend.app.services.ai_provider import build_ai_provider
from backend.app.services.usage_service import UsageService, rough_token_count


class MealService:
    def __init__(self, db: Session):
        self.db = db

    def create_uploaded_meal(self, user_id: int, image_path: str, note: str | None) -> Meal:
        meal = Meal(
            user_id=user_id,
            eaten_on=date.today(),
            meal_type=None,
            note=note,
            image_path=image_path,
            confidence="not_analyzed",
        )
        self.db.add(meal)
        self.db.commit()
        self.db.refresh(meal)
        return meal

    def analyze_image(self, meal_id: int) -> MealImageAnalysis:
        meal = self.db.get(Meal, meal_id)
        if meal is None or meal.image_path is None:
            raise ValueError("meal image not found")

        settings = get_settings()
        provider = build_ai_provider(settings.anthropic_api_key, settings.anthropic_model)
        result = provider.analyze_image(Path(meal.image_path), note=meal.note)
        UsageService(self.db).record(
            user_id=meal.user_id,
            task="image_analysis",
            provider=result.provider_status,
            model=result.used_model,
            estimated_tokens_in=result.estimated_tokens_in or rough_token_count(meal.note or ""),
            estimated_tokens_out=result.estimated_tokens_out,
        )

        if result.provider_status == "not_configured":
            payload = {
                "message": "Meal image analysis is unavailable until an AI provider is configured.",
                "detected_items": [],
                "calorie_range": [None, None],
                "macro_ranges": {},
                "confidence": "unavailable",
            }
        else:
            payload = self._parse_analysis_json(result.text)

        analysis = MealImageAnalysis(
            meal_id=meal.id,
            detected_items=payload.get("detected_items", []),
            follow_up_questions=payload.get("follow_up_questions", []),
            analysis_json=payload,
            provider_status=result.provider_status,
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def log_manual_meal(self, user_id: int, request: MealTextRequest) -> Meal:
        estimate = self._estimate_manual_meal(request.text)
        meal = Meal(
            user_id=user_id,
            eaten_on=request.eaten_on or date.today(),
            meal_type=request.meal_type,
            note=request.text,
            image_path=None,
            calories_min=estimate["calories_min"],
            calories_max=estimate["calories_max"],
            protein_min=estimate["protein_min"],
            protein_max=estimate["protein_max"],
            carbs_min=estimate["carbs_min"],
            carbs_max=estimate["carbs_max"],
            fat_min=estimate["fat_min"],
            fat_max=estimate["fat_max"],
            confidence=estimate["confidence"],
        )
        self.db.add(meal)
        self.db.flush()
        for item in estimate["items"]:
            self.db.add(
                MealItem(
                    meal_id=meal.id,
                    name=item["name"],
                    quantity=item.get("quantity"),
                    calories_min=item.get("calories_min"),
                    calories_max=item.get("calories_max"),
                    protein_min=item.get("protein_min"),
                    protein_max=item.get("protein_max"),
                    confidence=estimate["confidence"],
                )
            )
        self.db.commit()
        self.db.refresh(meal)
        return meal

    @staticmethod
    def serialize_meal(meal: Meal) -> dict:
        return {
            "id": meal.id,
            "note": meal.note,
            "image_path": meal.image_path,
            "calories_min": meal.calories_min,
            "calories_max": meal.calories_max,
            "protein_min": meal.protein_min,
            "protein_max": meal.protein_max,
            "carbs_min": meal.carbs_min,
            "carbs_max": meal.carbs_max,
            "fat_min": meal.fat_min,
            "fat_max": meal.fat_max,
            "confidence": meal.confidence,
        }

    @staticmethod
    def serialize_analysis(analysis: MealImageAnalysis) -> dict:
        payload = analysis.analysis_json or {}
        return {
            "id": analysis.id,
            "meal_id": analysis.meal_id,
            "provider_status": analysis.provider_status,
            "detected_items": analysis.detected_items or [],
            "follow_up_questions": analysis.follow_up_questions or [],
            "message": payload.get("message", ""),
            "analysis": payload,
        }

    @staticmethod
    def _parse_analysis_json(text: str) -> dict:
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        return {
            "message": text,
            "detected_items": [],
            "follow_up_questions": ["Tell me approximate portion sizes to improve accuracy."],
            "confidence": "low",
        }

    @staticmethod
    def _estimate_manual_meal(text: str) -> dict:
        normalized = text.lower()
        if "protein shake" in normalized:
            return {
                "calories_min": 120,
                "calories_max": 220,
                "protein_min": 25,
                "protein_max": 35,
                "carbs_min": 2,
                "carbs_max": 15,
                "fat_min": 1,
                "fat_max": 8,
                "confidence": "medium",
                "items": [
                    {
                        "name": "protein shake",
                        "quantity": "1 serving",
                        "calories_min": 120,
                        "calories_max": 220,
                        "protein_min": 25,
                        "protein_max": 35,
                    }
                ],
            }
        if "egg" in normalized:
            return {
                "calories_min": 140,
                "calories_max": 260,
                "protein_min": 12,
                "protein_max": 20,
                "carbs_min": 0,
                "carbs_max": 20,
                "fat_min": 8,
                "fat_max": 18,
                "confidence": "medium",
                "items": [{"name": "eggs", "quantity": "estimated serving"}],
            }
        if "pizza" in normalized:
            return {
                "calories_min": 500,
                "calories_max": 1000,
                "protein_min": 15,
                "protein_max": 40,
                "carbs_min": 55,
                "carbs_max": 130,
                "fat_min": 18,
                "fat_max": 55,
                "confidence": "low",
                "items": [{"name": "pizza", "quantity": "unknown portion"}],
            }
        return {
            "calories_min": 300,
            "calories_max": 700,
            "protein_min": 10,
            "protein_max": 35,
            "carbs_min": 20,
            "carbs_max": 90,
            "fat_min": 8,
            "fat_max": 35,
            "confidence": "low",
            "items": [{"name": "manual meal", "quantity": "unknown portion"}],
        }
