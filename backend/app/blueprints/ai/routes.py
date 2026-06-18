import os
import logging
from datetime import datetime, timezone, timedelta

from flask import Blueprint, request, g, Response, stream_with_context
from pydantic import ValidationError

import json as json_lib

from app.middleware.auth_middleware import require_auth
from app.utils.responses import success_response, error_response
from app.utils.rate_limiter import rate_limiter
from app.extensions import db
from app.repositories.ai_report_repository import AIReportRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.carbon_history_repository import CarbonHistoryRepository
from app.repositories.user_repository import UserRepository
from app.services.ai_service import AIService
from app.services.prompt_service import PromptService, sanitize_input
from app.blueprints.ai.schemas import (
    RecommendationsRequest,
    ChatRequest,
    WhatsIfRequest,
    FeedbackRequest,
)

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

    context = _build_user_context(g.user_id)
    data = {
        "score": body.score,
        "transport": body.transport,
        "food": body.food,
        "ac_usage": body.ac_usage,
        "level": context["level"],
        "streak": context["streak"],
        "weekly_avg": context["weekly_avg"],
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


@ai_bp.route("/chat", methods=["POST"])
@require_auth
@rate_limiter.limit(scope="user", capacity=30, refill_rate=1)
def chat():
    try:
        body = ChatRequest(**request.get_json(force=True))
    except ValidationError as exc:
        return error_response(str(exc), 422)

    context = _build_user_context(g.user_id)
    result = _ai_service.chat(g.user_id, body.message, context)
    if result is None:
        return error_response("AI service unavailable", 503)
    return success_response({"response": result})


@ai_bp.route("/chat/history", methods=["GET"])
@require_auth
def get_chat_history():
    history = _ai_service.get_conversation_history(g.user_id)
    return success_response(history)


@ai_bp.route("/chat/clear", methods=["POST"])
@require_auth
def clear_chat():
    _ai_service.clear_conversation(g.user_id)
    return success_response({"message": "Conversation cleared"})


@ai_bp.route("/what-if", methods=["POST"])
@require_auth
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


@ai_bp.route("/chat/stream", methods=["POST"])
@require_auth
@rate_limiter.limit(scope="user", capacity=20, refill_rate=1)
def chat_stream():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return error_response("Message is required", 422)

    message = sanitize_input(message, 1000)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return error_response("AI service not configured", 503)

    context = _build_user_context(g.user_id)
    history = _ai_service.get_conversation_history(g.user_id)
    prompt = PromptService().chat_response(message, context, history)

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:streamGenerateContent?alt=sse"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
    }
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 512},
    }

    def generate():
        import requests as http_requests

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
