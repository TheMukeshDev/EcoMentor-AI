import os
import hmac
import logging
from datetime import datetime, timezone, timedelta

from flask import Blueprint, request, g, Response, stream_with_context
from pydantic import ValidationError

import json as json_lib

from app.middleware.auth_middleware import require_auth
from app.middleware.csrf import csrf_protect
from app.utils.responses import success_response, error_response
from app.utils.rate_limiter import rate_limiter
from app.utils.safety import check_input_safety
from app.repositories.ai_report_repository import AIReportRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.carbon_history_repository import CarbonHistoryRepository
from app.repositories.user_repository import UserRepository
from app.services.ai_service import AIService
from app.services.prompt_service import sanitize_input
from app.blueprints.ai.schemas import (
    RecommendationsRequest,
    ChatRequest,
    WhatsIfRequest,
    FeedbackRequest,
)
from app.schemas.ai_schemas import SimulatorRequest
from app.services.coach_service import CoachService
from app.services.report_service import ReportService
from app.services.simulator_service import SimulatorService
from app.services.habit_service import HabitService
from app.services.forecast_service import ForecastService
from app.services.cache_service import CacheService
from app.services.dashboard_service import DashboardService

"""AI coaching blueprint routes for all Gemini-powered features.

Exposes endpoints for recommendations, chat, weekly reports,
eco-personalities, missions, forecasting, and coaching plans.
"""

logger = logging.getLogger(__name__)

ai_bp = Blueprint("ai", __name__)


def _get_db():
    from flask import current_app

    return current_app.extensions["firestore"]


def _get_ai_report_repo():
    return AIReportRepository(_get_db())


def _get_activity_repo():
    return ActivityRepository(_get_db())


def _get_carbon_history_repo():
    return CarbonHistoryRepository(_get_db())


def _get_user_repo():
    return UserRepository(_get_db())


def _get_ai_service():
    return AIService(
        api_key=os.getenv("GEMINI_API_KEY"),
        ai_report_repository=_get_ai_report_repo(),
    )


def _get_cache_service():
    return CacheService(_get_ai_report_repo())


def _get_coach_service():
    return CoachService(
        _get_ai_service(),
        _get_carbon_history_repo(),
        _get_activity_repo(),
        _get_user_repo(),
        _get_cache_service(),
    )


def _get_report_service():
    return ReportService(
        _get_ai_service(),
        _get_carbon_history_repo(),
        _get_user_repo(),
        _get_cache_service(),
    )


def _get_simulator_service():
    return SimulatorService(_get_ai_service(), _get_carbon_history_repo(), _get_user_repo())


def _get_habit_service():
    return HabitService(
        _get_ai_service(),
        _get_activity_repo(),
        _get_carbon_history_repo(),
        _get_user_repo(),
        _get_cache_service(),
    )


def _get_forecast_service():
    return ForecastService(_get_carbon_history_repo(), _get_user_repo())


def _get_dashboard_service():
    return DashboardService(
        carbon_history_repository=_get_carbon_history_repo(),
        activity_repository=_get_activity_repo(),
        user_repository=_get_user_repo(),
    )


@ai_bp.route("/recommendations", methods=["POST"])
@require_auth
@csrf_protect
@rate_limiter.limit(scope="user", capacity=30, refill_rate=1)
def get_recommendations():
    try:
        body = RecommendationsRequest(**request.get_json(force=True))
    except ValidationError as exc:
        return error_response(str(exc), 422)

    context = _get_dashboard_service().build_user_context(g.user_id)
    data = {
        "score": body.score,
        "transport": body.transport,
        "food": body.food,
        "ac_usage": body.ac_usage,
        "level": context["level"],
        "streak": context["streak"],
        "weekly_avg": context["weekly_avg"],
        "score_trend": context["score_trend"],
        "best_category": context["best_category"],
        "worst_category": context["worst_category"],
    }
    result = _get_ai_service().get_recommendations(g.user_id, data)
    if result is None:
        return error_response("AI service unavailable", 503)
    return success_response(result)


@ai_bp.route("/weekly-report", methods=["GET"])
@require_auth
@rate_limiter.limit(scope="user", capacity=10, refill_rate=1)
def get_weekly_report():
    context = _get_dashboard_service().build_user_context(g.user_id)
    result = _get_ai_service().get_weekly_report(g.user_id, context)
    if result is None:
        return error_response("AI service unavailable", 503)
    return success_response(result)


@ai_bp.route("/eco-personality", methods=["GET"])
@require_auth
@rate_limiter.limit(scope="user", capacity=10, refill_rate=1)
def get_eco_personality():
    context = _get_dashboard_service().build_user_context(g.user_id)
    result = _get_ai_service().get_eco_personality(g.user_id, context)
    if result is None:
        return error_response("AI service unavailable", 503)
    return success_response(result)


@ai_bp.route("/daily-mission", methods=["GET"])
@require_auth
@rate_limiter.limit(scope="user", capacity=20, refill_rate=1)
def get_daily_mission():
    user = _get_user_repo().get(g.user_id) or {}
    context = {"level": user.get("level", "Beginner")}
    result = _get_ai_service().get_daily_mission(g.user_id, context)
    if result is None:
        return error_response("AI service unavailable", 503)
    return success_response(result)


@ai_bp.route("/chat", methods=["POST"])
@require_auth
@csrf_protect
@rate_limiter.limit(scope="user", capacity=30, refill_rate=1)
def chat():
    try:
        body = ChatRequest(**request.get_json(force=True))
    except ValidationError as exc:
        return error_response(str(exc), 422)

    context = _get_dashboard_service().build_user_context(g.user_id)
    result = _get_ai_service().chat(g.user_id, body.message, context)
    if result is None:
        return error_response("AI service unavailable", 503)
    return success_response(result)


@ai_bp.route("/chat/history", methods=["GET"])
@require_auth
def get_chat_history():
    history = _get_ai_service().get_conversation_history(g.user_id)
    return success_response(history)


@ai_bp.route("/forecast", methods=["GET"])
@require_auth
@rate_limiter.limit(scope="user", capacity=20, refill_rate=1)
def get_forecast():
    context = _get_dashboard_service().build_user_context(g.user_id)
    rec_data = {
        "score": context["current_score"],
        "transport": "walking",
        "food": "vegetarian",
        "ac_usage": "none",
        "level": context["level"],
        "streak": context["streak"],
        "weekly_avg": context["weekly_avg"],
        "score_trend": context["score_trend"],
        "best_category": context["best_category"],
        "worst_category": context["worst_category"],
    }
    tips_dict = _get_ai_service().get_recommendations(g.user_id, rec_data)
    tips = tips_dict.get("tips", []) if isinstance(tips_dict, dict) else []

    result = _get_ai_service().get_carbon_savings_forecast(g.user_id, context, tips)
    if result is None:
        return error_response("AI service unavailable", 503)
    return success_response(result)


@ai_bp.route("/chat/clear", methods=["POST"])
@require_auth
@csrf_protect
def clear_chat():
    _get_ai_service().clear_conversation(g.user_id)
    return success_response({"message": "Conversation cleared"})


@ai_bp.route("/what-if", methods=["POST"])
@require_auth
@csrf_protect
@rate_limiter.limit(scope="user", capacity=10, refill_rate=1)
def whats_if():
    try:
        body = WhatsIfRequest(**request.get_json(force=True))
    except ValidationError as exc:
        return error_response(str(exc), 422)

    context = _get_dashboard_service().build_user_context(g.user_id)
    current_data = {
        "transport": body.transport,
        "distance": body.distance,
        "food_type": body.food_type,
        "ac_usage": body.ac_usage,
        "plastic_waste": body.plastic_waste,
    }
    scenario_changes = {
        "description": body.scenario_description,
    }
    result = _get_ai_service().whats_if(g.user_id, current_data, scenario_changes, context)
    if result is None:
        return error_response("AI service unavailable", 503)
    return success_response(result)


@ai_bp.route("/feedback", methods=["POST"])
@require_auth
@csrf_protect
@rate_limiter.limit(scope="user", capacity=20, refill_rate=1)
def feedback():
    try:
        body = FeedbackRequest(**request.get_json(force=True))
    except ValidationError as exc:
        return error_response(str(exc), 422)

    context = _get_dashboard_service().build_user_context(g.user_id)
    result = _get_ai_service().submit_feedback(g.user_id, body.feedback_type, body.message, context)
    if result is None:
        return error_response("AI service unavailable", 503)
    return success_response(result)


def _save_stream_conversation(user_id, user_message, response_parts):
    text = "".join(response_parts)
    now = datetime.now(timezone.utc).isoformat()
    service = _get_ai_service()
    history = service.get_conversation_history(user_id)
    service._summarize_and_compact(user_id)
    history = service.get_conversation_history(user_id)
    history.append({"role": "user", "content": user_message, "timestamp": now})
    history.append({"role": "assistant", "content": text, "timestamp": now})
    if len(history) > 50:
        history = history[-50:]
    service._conversations[user_id] = history
    service._persist_conversation(user_id, history)


@ai_bp.route("/chat/stream", methods=["POST"])
@require_auth
@csrf_protect
@rate_limiter.limit(scope="user", capacity=20, refill_rate=1)
def chat_stream():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return error_response("Message is required", 422)

    message = sanitize_input(message, 1000)

    safety = check_input_safety(message)
    if not safety["safe"]:
        logger.warning("Unsafe stream input from %s: %s", g.user_id, safety["issues"])
        return error_response("Message contains prohibited content", 422)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return error_response("AI service not configured", 503)

    user_id = g.user_id
    _get_dashboard_service().build_user_context(user_id)
    history = _get_ai_service().get_conversation_history(user_id)

    contents = []
    for msg in history[-20:]:
        raw_role = msg.get("role", "user")
        gemini_role = "model" if raw_role in ("assistant", "system") else "user"
        contents.append({"role": gemini_role, "parts": [{"text": msg.get("content", "")}]})
    contents.append({"role": "user", "parts": [{"text": message}]})

    system_prompt = "You are EcoMentor, an AI sustainability coach. Help users understand and reduce their carbon footprint. Respond conversationally and helpfully. Keep responses under 150 words."
    from app.services.ai_service import GEMINI_API_BASE, GEMINI_MODEL

    url = f"{GEMINI_API_BASE}/{GEMINI_MODEL}:streamGenerateContent?alt=sse"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
    }
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 512, "seed": 42},
        "safetySettings": [
            {"category": c, "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
            for c in [
                "HARM_CATEGORY_HARASSMENT",
                "HARM_CATEGORY_DANGEROUS_CONTENT",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "HARM_CATEGORY_HATE_SPEECH",
            ]
        ],
    }

    full_response = []

    def generate():
        import requests as http_requests

        nonlocal full_response

        try:
            resp = http_requests.post(url, headers=headers, json=payload, stream=True, timeout=30)
            if resp.status_code != 200:
                yield f"data: {json_lib.dumps({'error': 'AI service error'})}\n\n"
                yield "data: [DONE]\n\n"
                return
            for line in resp.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith("data: "):
                        chunk = line[6:]
                        if chunk == "[DONE]":
                            _save_stream_conversation(user_id, message, full_response)
                            yield "data: [DONE]\n\n"
                            return
                        try:
                            parsed = json_lib.loads(chunk)
                            candidates = parsed.get("candidates", [])
                            if candidates:
                                content = candidates[0].get("content", {})
                                parts = content.get("parts", [])
                                if parts:
                                    text = parts[0].get("text", "")
                                    if text:
                                        full_response.append(text)
                                        yield f"data: {json_lib.dumps({'text': text})}\n\n"
                        except json_lib.JSONDecodeError:
                            continue
        except Exception as exc:
            logger.error("Stream error: %s", exc)
            yield f"data: {json_lib.dumps({'error': 'Stream error'})}\n\n"
            yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── 5 Core AI Features ───────────────────────────────────────────


@ai_bp.route("/coach", methods=["GET"])
@require_auth
@rate_limiter.limit(scope="user", capacity=20, refill_rate=1)
def get_coach():
    """Personalized carbon coaching plan (cached 24h per user)."""
    result = _get_coach_service().get_coaching_plan(g.user_id)
    return success_response(result)


@ai_bp.route("/sustainability-report", methods=["GET"])
@require_auth
@rate_limiter.limit(scope="user", capacity=10, refill_rate=1)
def get_sustainability_report():
    """Weekly sustainability report with AI insights."""
    result = _get_report_service().generate_report(g.user_id)
    return success_response(result)


@ai_bp.route("/internal/weekly-report", methods=["POST"])
def trigger_weekly_report():
    """Cloud Scheduler trigger for weekly reports (internal only)."""
    api_key = request.headers.get("X-Internal-Key", "")
    expected = os.getenv("INTERNAL_API_KEY", "")
    if not expected or not hmac.compare_digest(api_key, expected):
        return error_response("Unauthorized", 401)
    return success_response({"triggered": True})


@ai_bp.route("/whatif", methods=["POST"])
@require_auth
@csrf_protect
@rate_limiter.limit(scope="user", capacity=10, refill_rate=1)
def whatif_simulator():
    """What-If Simulator for hypothetical lifestyle changes."""
    try:
        body = SimulatorRequest(**request.get_json(force=True))
    except ValidationError as exc:
        return error_response(str(exc), 422)

    result = _get_simulator_service().simulate(g.user_id, body.scenario)
    return success_response(result)


@ai_bp.route("/habits", methods=["GET"])
@require_auth
@rate_limiter.limit(scope="user", capacity=20, refill_rate=1)
def get_habits():
    """Habit suggestions using rule engine + AI personalization."""
    result = _get_habit_service().get_habits(g.user_id)
    return success_response(result)


@ai_bp.route("/carbon-forecast", methods=["GET"])
@require_auth
@rate_limiter.limit(scope="user", capacity=20, refill_rate=1)
def get_carbon_forecast():
    """Carbon emission forecast using linear regression."""
    days = request.args.get("days", 30, type=int)
    result = _get_forecast_service().get_forecast(g.user_id, days)
    return success_response(result)
