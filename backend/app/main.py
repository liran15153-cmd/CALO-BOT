from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.body_metrics import router as body_metrics_router
from backend.app.api.chat import router as chat_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.meals import router as meals_router
from backend.app.api.onboarding import router as onboarding_router
from backend.app.api.pending_actions import router as pending_actions_router
from backend.app.api.settings import router as settings_router
from backend.app.api.usage import router as usage_router
from backend.app.api.workouts import logs_router, router as workout_plans_router, workouts_router
from backend.app.config import get_settings
from backend.app.db import init_db
from backend.app.schemas import HealthResponse
from backend.app.services.readiness_service import ReadinessService


settings = get_settings()

app = FastAPI(title="CALO Coach API", version="0.1.0")
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    messages = [_hebrew_validation_message(str(error.get("msg") or "")) for error in exc.errors()]
    hebrew_messages = [message for message in messages if message]
    return JSONResponse(
        status_code=422,
        content={"detail": hebrew_messages or ["בקשת API לא תקינה. יש לבדוק את השדות והערכים שנשלחו."]},
    )


def _hebrew_validation_message(message: str) -> str | None:
    for prefix in ("Value error, ", "Assertion failed, "):
        if message.startswith(prefix):
            message = message.removeprefix(prefix)
    return message if any("\u0590" <= char <= "\u05ff" for char in message) else None


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    current_settings = get_settings()
    return HealthResponse(
        status="ok",
        service="calo-coach",
        database="configured" if current_settings.database_url else "not_configured",
        ai_provider=current_settings.ai_provider_status,
        no_api_key_mode=current_settings.ai_provider_status == "not_configured",
    )


@app.get("/api/readiness")
def readiness() -> dict:
    return ReadinessService(get_settings()).status()


app.include_router(onboarding_router)
app.include_router(chat_router)
app.include_router(pending_actions_router)
app.include_router(workout_plans_router)
app.include_router(logs_router)
app.include_router(workouts_router)
app.include_router(meals_router)
app.include_router(dashboard_router)
app.include_router(body_metrics_router)
app.include_router(settings_router)
app.include_router(usage_router)
