from datetime import date
import json
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.models import Meal, MealImageAnalysis, MealItem
from backend.app.schemas import MealTextRequest
from backend.app.services.ai_provider import build_ai_provider
from backend.app.services.language_guard import contains_hebrew, has_disallowed_latin_text
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
            raise ValueError("תמונת הארוחה לא נמצאה")

        settings = get_settings()
        usage_service = UsageService(self.db)
        if settings.anthropic_api_key and usage_service.is_daily_ai_token_budget_exceeded():
            usage_service.record(
                user_id=meal.user_id,
                task="image_analysis",
                provider="budget_exceeded",
                model=None,
                estimated_tokens_in=0,
                estimated_tokens_out=0,
            )
            payload = {
                "message": (
                    "תקציב הבינה המלאכותית היומי נוצל. ניתוח תמונת הארוחה לא נשלח לספק הבינה המלאכותית."
                ),
                "detected_items": [],
                "calorie_range": [None, None],
                "macro_ranges": {},
                "confidence": "unavailable",
            }
            analysis = MealImageAnalysis(
                meal_id=meal.id,
                detected_items=[],
                follow_up_questions=[],
                analysis_json=payload,
                provider_status="budget_exceeded",
            )
            self.db.add(analysis)
            self.db.commit()
            self.db.refresh(analysis)
            return analysis

        provider = build_ai_provider(settings.anthropic_api_key, settings.anthropic_model)
        result = provider.analyze_image(Path(meal.image_path), note=meal.note)
        usage_service.record(
            user_id=meal.user_id,
            task="image_analysis",
            provider=result.provider_status,
            model=result.used_model,
            estimated_tokens_in=result.estimated_tokens_in or rough_token_count(meal.note or ""),
            estimated_tokens_out=result.estimated_tokens_out,
        )

        if result.provider_status == "not_configured":
            payload = {
                "message": "ניתוח תמונת ארוחה לא זמין עד שמוגדר ספק בינה מלאכותית.",
                "detected_items": [],
                "calorie_range": [None, None],
                "macro_ranges": {},
                "confidence": "unavailable",
            }
        elif result.provider_status == "provider_error":
            payload = {
                "message": result.text,
                "detected_items": [],
                "calorie_range": [None, None],
                "macro_ranges": {},
                "confidence": "unavailable",
            }
        else:
            payload = self._parse_analysis_json(result.text)
            self._apply_image_estimate(meal, payload)

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
                return MealService._ensure_hebrew_analysis_payload(parsed)
        except json.JSONDecodeError:
            pass
        return MealService._ensure_hebrew_analysis_payload(
            {
            "message": text,
            "detected_items": [],
            "follow_up_questions": ["כתוב לי כמויות משוערות כדי לשפר את הדיוק."],
            "confidence": "low",
            }
        )

    @staticmethod
    def _ensure_hebrew_analysis_payload(payload: dict) -> dict:
        normalized = dict(payload)
        message = normalized.get("message")
        if isinstance(message, str) and message.strip() and (
            not contains_hebrew(message) or has_disallowed_latin_text(message)
        ):
            normalized["message"] = "ניתוח התמונה חזר עם טקסט שרובו לא בעברית, ולכן מוצגת הערכה שמרנית בלבד."

        normalized["detected_items"] = [
            MealService._ensure_hebrew_detected_item(item)
            for item in normalized.get("detected_items", [])
            if isinstance(item, dict)
        ]

        questions = [
            question
            for question in normalized.get("follow_up_questions", [])
            if isinstance(question, str) and contains_hebrew(question) and not has_disallowed_latin_text(question)
        ]
        if normalized.get("follow_up_questions") and not questions:
            questions = ["מה הכמות המשוערת ומה שיטת ההכנה?"]
        normalized["follow_up_questions"] = questions
        return normalized

    @staticmethod
    def _ensure_hebrew_detected_item(item: dict) -> dict:
        normalized = dict(item)
        name = str(normalized.get("name") or "").strip()
        quantity = str(normalized.get("quantity") or "").strip()
        if name and (not contains_hebrew(name) or has_disallowed_latin_text(name)):
            normalized["name"] = "פריט מזון שזוהה"
        if quantity and (not contains_hebrew(quantity) or has_disallowed_latin_text(quantity)):
            normalized["quantity"] = "כמות לא ודאית"
        return normalized

    def _apply_image_estimate(self, meal: Meal, payload: dict) -> None:
        calories = self._range_from_payload(payload, "calorie_range", "calories_range")
        protein = self._macro_range(payload, "protein")
        carbs = self._macro_range(payload, "carbs")
        fat = self._macro_range(payload, "fat")

        meal.calories_min, meal.calories_max = calories
        meal.protein_min, meal.protein_max = protein
        meal.carbs_min, meal.carbs_max = carbs
        meal.fat_min, meal.fat_max = fat
        meal.confidence = self._confidence(payload.get("confidence"))

        detected_items = [item for item in payload.get("detected_items", []) if isinstance(item, dict)]
        self.db.execute(delete(MealItem).where(MealItem.meal_id == meal.id))
        for item in detected_items:
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            item_calories = self._range_from_item(item, "calories")
            item_protein = self._range_from_item(item, "protein")
            self.db.add(
                MealItem(
                    meal_id=meal.id,
                    name=name[:160],
                    quantity=str(item.get("quantity") or "").strip()[:120] or None,
                    calories_min=item_calories[0],
                    calories_max=item_calories[1],
                    protein_min=item_protein[0],
                    protein_max=item_protein[1],
                    confidence=meal.confidence,
                )
            )

    @classmethod
    def _range_from_payload(cls, payload: dict, *keys: str) -> tuple[int | None, int | None]:
        for key in keys:
            value = payload.get(key)
            parsed = cls._number_range(value)
            if parsed != (None, None):
                return parsed
        return None, None

    @classmethod
    def _macro_range(cls, payload: dict, macro_name: str) -> tuple[int | None, int | None]:
        macro_ranges = payload.get("macro_ranges")
        if not isinstance(macro_ranges, dict):
            return None, None
        return cls._number_range(macro_ranges.get(macro_name))

    @classmethod
    def _range_from_item(cls, item: dict, prefix: str) -> tuple[int | None, int | None]:
        direct = cls._number_range(item.get(f"{prefix}_range"))
        if direct != (None, None):
            return direct
        return cls._ordered_pair(item.get(f"{prefix}_min"), item.get(f"{prefix}_max"))

    @staticmethod
    def _number_range(value: object) -> tuple[int | None, int | None]:
        if not isinstance(value, list | tuple) or len(value) != 2:
            return None, None
        return MealService._ordered_pair(value[0], value[1])

    @staticmethod
    def _ordered_pair(min_value: object, max_value: object) -> tuple[int | None, int | None]:
        if not isinstance(min_value, int | float) or not isinstance(max_value, int | float):
            return None, None
        low = max(0, int(min_value))
        high = max(0, int(max_value))
        if high < low:
            low, high = high, low
        return low, high

    @staticmethod
    def _confidence(value: object) -> str:
        if value in {"low", "medium", "high"}:
            return str(value)
        return "low"

    @staticmethod
    def _estimate_manual_meal(text: str) -> dict:
        normalized = text.lower()
        items = []
        if "protein shake" in normalized or "שייק חלבון" in normalized or "אבקת חלבון" in normalized:
            items.append(
                {
                    "name": "שייק חלבון",
                    "quantity": "מנה משוערת",
                    "calories_min": 120,
                    "calories_max": 220,
                    "protein_min": 25,
                    "protein_max": 35,
                    "carbs_min": 2,
                    "carbs_max": 15,
                    "fat_min": 1,
                    "fat_max": 8,
                }
            )
        if "greek yogurt" in normalized or "yogurt" in normalized or "יוגורט" in normalized:
            items.append(
                {
                    "name": "יוגורט יווני",
                    "quantity": "מנה משוערת",
                    "calories_min": 90,
                    "calories_max": 160,
                    "protein_min": 10,
                    "protein_max": 20,
                    "carbs_min": 4,
                    "carbs_max": 15,
                    "fat_min": 0,
                    "fat_max": 8,
                }
            )
        if "banana" in normalized or "בננה" in normalized:
            items.append(
                {
                    "name": "בננה",
                    "quantity": "יחידה משוערת",
                    "calories_min": 80,
                    "calories_max": 130,
                    "protein_min": 1,
                    "protein_max": 2,
                    "carbs_min": 18,
                    "carbs_max": 32,
                    "fat_min": 0,
                    "fat_max": 1,
                }
            )
        if items:
            return {
                "calories_min": sum(item["calories_min"] for item in items),
                "calories_max": sum(item["calories_max"] for item in items),
                "protein_min": sum(item["protein_min"] for item in items),
                "protein_max": sum(item["protein_max"] for item in items),
                "carbs_min": sum(item["carbs_min"] for item in items),
                "carbs_max": sum(item["carbs_max"] for item in items),
                "fat_min": sum(item["fat_min"] for item in items),
                "fat_max": sum(item["fat_max"] for item in items),
                "confidence": "medium",
                "items": items,
            }
        if "protein shake" in normalized or "שייק חלבון" in normalized or "אבקת חלבון" in normalized:
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
                        "name": "שייק חלבון",
                        "quantity": "מנה משוערת",
                        "calories_min": 120,
                        "calories_max": 220,
                        "protein_min": 25,
                        "protein_max": 35,
                    }
                ],
            }
        if "egg" in normalized or "ביצה" in normalized or "ביצים" in normalized:
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
                "items": [{"name": "ביצים", "quantity": "מנה משוערת"}],
            }
        if "pizza" in normalized or "פיצה" in normalized:
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
                "items": [{"name": "פיצה", "quantity": "כמות לא ידועה"}],
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
            "items": [{"name": "ארוחה ידנית", "quantity": "כמות לא ידועה"}],
        }
