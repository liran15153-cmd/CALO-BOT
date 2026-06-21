from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.body_metrics import router as body_metrics_router
from backend.app.api.chat import router as chat_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.meals import router as meals_router
from backend.app.api.onboarding import router as onboarding_router
from backend.app.api.pending_actions import router as pending_actions_router
from backend.app.api.settings import router as settings_router
from backend.app.api.summaries import router as summaries_router
from backend.app.api.usage import router as usage_router
from backend.app.api.workouts import logs_router, router as workout_plans_router, workouts_router
from backend.app.config import get_settings
from backend.app.db import init_db
from backend.app.schemas import HealthResponse


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


app.include_router(onboarding_router)
app.include_router(chat_router)
app.include_router(pending_actions_router)
app.include_router(workout_plans_router)
app.include_router(logs_router)
app.include_router(workouts_router)
app.include_router(meals_router)
app.include_router(summaries_router)
app.include_router(dashboard_router)
app.include_router(body_metrics_router)
app.include_router(settings_router)
app.include_router(usage_router)
