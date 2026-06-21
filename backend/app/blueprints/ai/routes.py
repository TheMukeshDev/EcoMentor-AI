import os
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
from app.extensions import db
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

logger = logging.getLogger(__name__)

ai_bp = Blueprint("ai", __name__)

_ai_report_repo = AIReportRepository(db)
_activity_repo = ActivityRepository(db)
_carbon_history_repo = CarbonHistoryRepository(db)
_user_repo = UserRepository(db)
_ai_service = AIService(
    api_key=os.getenv("GEMINI_API_KEY"),
    ai_report_repository=_ai_report_repo,
)
_cache_service = CacheService(_ai_report_repo)
_coach_service = CoachService(
    _ai_service, _carbon_history_repo, _activity_repo, _user_repo, _cache_service
)
_report_service = ReportService(
    _ai_service, _carbon_history_repo, _user_repo, _cache_service
)
_simulator_service = SimulatorService(
    _ai_service, _carbon_history_repo, _user_repo
)
_habit_service = HabitService(
    _ai_service, _activity_repo, _carbon_history_repo, _user_repo, _cache_service
)
_forecast_service = ForecastService(_carbon_history_repo, _user_repo)


def _compute_trend(scores):
    if len(scores) < 2:
        return "stable"
    window = scores[-3:] if len(scores) >= 3 else scores
    if window[-1] < window[0]:
        return "improving"
    if window[-1] > window[0]:
        return "declining"
    return "stable"


def _best_worst_category(week_entries):
    totals = {}
    counts = {}
    for e in week_entries:
        for cat in ("transport", "electricity", "food", "waste"):
            val = e.get(cat, 0)
            if val:
                totals[cat] = totals.get(cat, 0) + val
                counts[cat] = counts.get(cat, 0) + 1
    avgs = {c: (totals[c] / counts[c] if counts.get(c) else 0) for c in totals}
    if not avgs:
        return "transport", "transport"
    worst = max(avgs, key=avgs.get)
    best = min(avgs, key=avgs.get)
    return best, worst


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
    best_cat, worst_cat = _best_worst_category(week_entries)

    return {
        "level": user.get("level", "Beginner"),
        "streak": user.get("streak", 0),
        "weekly_avg": weekly_avg,
        "current_score": scores[-1] if scores else 0,
        "activity_count": len(activities),
        "score_trend": _compute_trend(scores),
        "best_category": best_cat,
        "worst_category": worst_cat,
        "score_history": scores[-7:] if scores else [],
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
@csrf_protect
@rate_limiter.limit(scope="user", capacity=30, refill_rate=1)
def get_recommendations():
    try:
        body = RecommendationsRequest(**request.get_json(force=True))
    except ValidationError as exc:
        return error_response(str(exc), 422)

    context = _build_user_context(g.user_id)
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
    result = _ai_service.get_recommendations(g.user_id, data)
    if result is None:
        return error_response("AI service unavailable", 503)
    return success_response(result)


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


@ai_bp.route("/chat", methods=["POST"])
@require_auth
@csrf_protect
@rate_limiter.limit(scope="user", capacity=30, refill_rate=1)
def chat():
    try:
        body = ChatRequest(**request.get_json(force=True))
    except ValidationError as exc:
        return error_response(str(exc), 422)

    safety = check_input_safety(body.message)
    if not safety["safe"]:
        logger.warning("Unsafe chat input from %s: %s", g.user_id, safety["issues"])
        return error_response("Message contains prohibited content", 422)

    context = _build_user_context(g.user_id)
    result = _ai_service.chat(g.user_id, body.message, context)
    if result is None:
        return error_response("AI service unavailable", 503)
    return success_response(result)


@ai_bp.route("/chat/history", methods=["GET"])
@require_auth
def get_chat_history():
    history = _ai_service.get_conversation_history(g.user_id)
    return success_response(history)


@ai_bp.route("/forecast", methods=["GET"])
@require_auth
@rate_limiter.limit(scope="user", capacity=20, refill_rate=1)
def get_forecast():
    context = _build_user_context(g.user_id)
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
    tips_dict = _ai_service.get_recommendations(g.user_id, rec_data)
    tips = tips_dict.get("tips", []) if isinstance(tips_dict, dict) else []

    result = _ai_service.get_carbon_savings_forecast(g.user_id, context, tips)
    if result is None:
        return error_response("AI service unavailable", 503)
    return success_response(result)



@ai_bp.route("/chat/clear", methods=["POST"])
@require_auth
@csrf_protect
def clear_chat():
    _ai_service.clear_conversation(g.user_id)
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

    context = _build_user_context(g.user_id)
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
    result = _ai_service.whats_if(g.user_id, current_data, scenario_changes, context)
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

    context = _build_user_context(g.user_id)
    result = _ai_service.submit_feedback(
        g.user_id, body.feedback_type, body.message, context
    )
    if result is None:
        return error_response("AI service unavailable", 503)
    return success_response(result)


def _save_stream_conversation(user_id, user_message, response_parts):
    text = "".join(response_parts)
    now = datetime.now(timezone.utc).isoformat()
    history = _ai_service.get_conversation_history(user_id)
    _ai_service._summarize_and_compact(user_id)
    history = _ai_service.get_conversation_history(user_id)
    history.append({"role": "user", "content": user_message, "timestamp": now})
    history.append({"role": "assistant", "content": text, "timestamp": now})
    if len(history) > 50:
        history = history[-50:]
    _ai_service._conversations[user_id] = history
    _ai_service._persist_conversation(user_id, history)


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

    _build_user_context(g.user_id)
    history = _ai_service.get_conversation_history(g.user_id)

    contents = []
    for msg in history[-20:]:
        raw_role = msg.get("role", "user")
        gemini_role = "model" if raw_role in ("assistant", "system") else "user"
        contents.append(
            {"role": gemini_role, "parts": [{"text": msg.get("content", "")}]}
        )
    contents.append({"role": "user", "parts": [{"text": message}]})

    system_prompt = "You are EcoMentor, an AI sustainability coach. Help users understand and reduce their carbon footprint. Respond conversationally and helpfully. Keep responses under 150 words."
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:streamGenerateContent?alt=sse"
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
            resp = http_requests.post(
                url, headers=headers, json=payload, stream=True, timeout=30
            )
            if resp.status_code != 200:
                yield f"data: {json_lib.dumps({'error': 'AI service error'})}\n\n"
                yield "data: [DONE]\n\n"
                return
            for line in resp.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith("data: "):
                        chunk = line[6:]
                        if chunk == "[DONE]":
                            _save_stream_conversation(g.user_id, message, full_response)
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
    result = _coach_service.get_coaching_plan(g.user_id)
    return success_response(result)


@ai_bp.route("/sustainability-report", methods=["GET"])
@require_auth
@rate_limiter.limit(scope="user", capacity=10, refill_rate=1)
def get_sustainability_report():
    """Weekly sustainability report with AI insights."""
    result = _report_service.generate_report(g.user_id)
    return success_response(result)


@ai_bp.route("/internal/weekly-report", methods=["POST"])
def trigger_weekly_report():
    """Cloud Scheduler trigger for weekly reports (internal only)."""
    api_key = request.headers.get("X-Internal-Key", "")
    expected = os.getenv("INTERNAL_API_KEY", "")
    if not expected or api_key != expected:
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

    result = _simulator_service.simulate(g.user_id, body.scenario)
    return success_response(result)


@ai_bp.route("/habits", methods=["GET"])
@require_auth
@rate_limiter.limit(scope="user", capacity=20, refill_rate=1)
def get_habits():
    """Habit suggestions using rule engine + AI personalization."""
    result = _habit_service.get_habits(g.user_id)
    return success_response(result)


@ai_bp.route("/carbon-forecast", methods=["GET"])
@require_auth
@rate_limiter.limit(scope="user", capacity=20, refill_rate=1)
def get_carbon_forecast():
    """Carbon emission forecast using linear regression."""
    days = request.args.get("days", 30, type=int)
    result = _forecast_service.get_forecast(g.user_id, days)
    return success_response(result)

