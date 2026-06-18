import os
from datetime import datetime, timezone, timedelta

from flask import Blueprint, request, g
from pydantic import ValidationError

from app.middleware.auth_middleware import require_auth
from app.utils.responses import success_response, error_response
from app.utils.rate_limiter import rate_limiter
from app.extensions import db
from app.repositories.ai_report_repository import AIReportRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.carbon_history_repository import CarbonHistoryRepository
from app.repositories.user_repository import UserRepository
from app.services.ai_service import AIService
from app.blueprints.ai.schemas import RecommendationsRequest

ai_bp = Blueprint("ai", __name__)

_ai_report_repo = AIReportRepository(db)
_activity_repo = ActivityRepository(db)
_carbon_history_repo = CarbonHistoryRepository(db)
_user_repo = UserRepository(db)
_ai_service = AIService(
    api_key=os.getenv("GEMINI_API_KEY"),
    ai_report_repository=_ai_report_repo,
)


def _build_user_context(user_id):
    user = _user_repo.get(user_id) or {}
    today = datetime.now(timezone.utc)
    seven_days_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    week_entries = _carbon_history_repo.find_by_user_and_date_range(
        user_id, seven_days_ago, today.strftime("%Y-%m-%d")
    )
    scores = [e.get("carbon_score", 0) for e in week_entries]
    weekly_avg = round(sum(scores) / len(scores), 2) if scores else 0
    activities = _activity_repo.find_by_user_id(user_id)

    return {
        "level": user.get("level", "Beginner"),
        "streak": user.get("streak", 0),
        "weekly_avg": weekly_avg,
        "current_score": scores[-1] if scores else 0,
        "activity_count": len(activities),
        "weekly_data": {
            "transport_avg": _avg_field(week_entries, "transport"),
            "electricity_avg": _avg_field(week_entries, "electricity"),
            "food_avg": _avg_field(week_entries, "food"),
            "waste_avg": _avg_field(week_entries, "waste"),
        },
    }


def _avg_field(entries, field):
    vals = [e.get(field, 0) for e in entries]
    return round(sum(vals) / len(vals), 2) if vals else 0


@ai_bp.route("/recommendations", methods=["POST"])
@require_auth
@rate_limiter.limit(scope="user", capacity=30, refill_rate=1)
def get_recommendations():
    try:
        body = RecommendationsRequest(**request.get_json(force=True))
    except ValidationError as exc:
        return error_response(str(exc), 422)

    data = {
        "score": body.score,
        "transport": body.transport,
        "food": body.food,
        "ac_usage": body.ac_usage,
    }
    result = _ai_service.get_recommendations(g.user_id, data)
    if result is None:
        return error_response("AI service unavailable", 503)
    return success_response({"tips": result})


@ai_bp.route("/weekly-report", methods=["GET"])
@require_auth
@rate_limiter.limit(scope="user", capacity=10, refill_rate=1)
def get_weekly_report():
    context = _build_user_context(g.user_id)
    result = _ai_service.get_weekly_report(g.user_id, context)
    if result is None:
        return error_response("AI service unavailable", 503)
    return success_response(result)


@ai_bp.route("/eco-personality", methods=["GET"])
@require_auth
@rate_limiter.limit(scope="user", capacity=10, refill_rate=1)
def get_eco_personality():
    context = _build_user_context(g.user_id)
    result = _ai_service.get_eco_personality(g.user_id, context)
    if result is None:
        return error_response("AI service unavailable", 503)
    return success_response(result)


@ai_bp.route("/daily-mission", methods=["GET"])
@require_auth
@rate_limiter.limit(scope="user", capacity=20, refill_rate=1)
def get_daily_mission():
    user = _user_repo.get(g.user_id) or {}
    context = {"level": user.get("level", "Beginner")}
    result = _ai_service.get_daily_mission(g.user_id, context)
    if result is None:
        return error_response("AI service unavailable", 503)
    return success_response(result)
