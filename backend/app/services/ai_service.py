import json
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

import requests

from app.services.prompt_service import PromptService
from app.services.cache_service import CacheService
from app.services.carbon_service import estimate_gemini_carbon
from app.utils.safety import (
    check_input_safety,
    check_output_safety,
    filter_unsafe_output,
)
from app.extensions import db

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODEL = "gemini-2.0-flash"
MAX_RETRIES = 3
RETRY_DELAY = 1.0
CONVERSATION_TTL_DAYS = int(os.getenv("CONVERSATION_TTL_DAYS", "7"))

_FALLBACKS = {
    "recommendations": [
        "Try walking or cycling for short trips instead of driving",
        "Switch to energy-efficient LED bulbs at home",
        "Reduce food waste by planning meals ahead",
    ],
    "weekly_report": {
        "biggest_contributor": "Transport",
        "best_improvement": "Keep logging your daily activities to discover trends",
        "next_week_goal": "Reduce your carbon score by 5 points",
        "summary": "You are building awareness of your carbon footprint. Consistent logging helps identify patterns and opportunities for improvement.",
    },
    "eco_personality": {
        "personality": "Eco Explorer",
        "strength": "Starting your sustainability journey",
        "weakness": "Building consistent habits",
        "next_goal": "Log activities daily for a week",
    },
    "daily_mission": {
        "challenge": "Log today's activities to track your carbon footprint",
        "reward": 50,
    },
}


class AIService:
    def __init__(self, api_key=None, ai_report_repository=None):
        self._api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._prompts = PromptService()
        self._cache = CacheService(ai_report_repository)
        self._conversations = {}

    def get_recommendations(self, user_id, data):
        cached = self._cache.get(user_id, "recommendations")
        if cached:
            return cached

        prompt = self._prompts.recommendations(data)
        result = self._call_gemini(prompt, deterministic=True)
        if result:
            self._cache.set(user_id, "recommendations", result)
            return result
        return _FALLBACKS["recommendations"]

    def get_weekly_report(self, user_id, user_context):
        cached = self._cache.get(user_id, "weekly_report")
        if cached:
            return cached

        prompt = self._prompts.weekly_report(user_context)
        result = self._call_gemini(prompt, deterministic=True)
        if result:
            self._cache.set(user_id, "weekly_report", result)
            return result
        return _FALLBACKS["weekly_report"]

    def get_eco_personality(self, user_id, user_context):
        cached = self._cache.get(user_id, "eco_personality")
        if cached:
            return cached

        prompt = self._prompts.eco_personality(user_context)
        result = self._call_gemini(prompt, deterministic=True)
        if result:
            self._cache.set(user_id, "eco_personality", result)
            return result
        return _FALLBACKS["eco_personality"]

    def get_daily_mission(self, user_id, user_context):
        cached = self._cache.get(user_id, "daily_mission")
        if cached:
            return cached

        prompt = self._prompts.daily_mission(user_context)
        result = self._call_gemini(prompt, deterministic=True)
        if result:
            self._cache.set(user_id, "daily_mission", result)
            return result
        return _FALLBACKS["daily_mission"]

    def _summarize_and_compact(self, user_id):
        history = self._conversations.get(user_id, [])
        if len(history) < 40:
            return

        recent = history[-20:]
        older = history[:-20]

        lines = []
        for msg in older:
            role = msg.get("role", "user")
            content = msg.get("content", "")[:200]
            lines.append(f"{role}: {content}")
        conv_text = "\n".join(lines)

        prompt = (
            "Summarize the following eco-coaching conversation in 2-3 sentences. "
            "Capture the user's main concerns, their context, and any suggestions given.\n\n"
            f"{conv_text}\n\n"
            'Return ONLY valid JSON: {"summary": "your 2-3 sentence summary here"}'
        )

        result = self._call_gemini(prompt, deterministic=True)
        if result and isinstance(result, dict) and "summary" in result:
            summary_text = result["summary"]
            summary_entry = {
                "role": "system",
                "content": f"Previous conversation summary: {summary_text}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._conversations[user_id] = [summary_entry] + recent
            logger.info(
                "Summarized conversation for user %s (%d messages -> 1 summary + %d recent)",
                user_id,
                len(older),
                len(recent),
            )
        else:
            self._conversations[user_id] = history[-40:]
            logger.info(
                "Summarization failed for user %s, truncated to last 40 messages",
                user_id,
            )

    def chat(self, user_id, user_message, user_context):
        safety = check_input_safety(user_message)
        if not safety["safe"]:
            logger.warning("Unsafe chat input from %s: %s", user_id, safety["issues"])
            return "I'm here to discuss sustainability and eco-friendly topics. Let's keep our conversation focused on reducing your carbon footprint!"

        self._ensure_conversation_loaded(user_id)
        history = self._conversations[user_id]
        self._summarize_and_compact(user_id)
        history = self._conversations[user_id]
        prompt = self._prompts.chat_response(user_message, user_context, history)
        result = self._call_gemini(prompt)
        if result and isinstance(result, dict) and "response" in result:
            clean_response = filter_unsafe_output(result["response"])
            history.append(
                {
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            history.append(
                {
                    "role": "assistant",
                    "content": clean_response,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            if len(history) > 50:
                self._conversations[user_id] = history[-50:]
            self._persist_conversation(user_id, history)
            return clean_response
        return "I'm here to help with your sustainability questions. Could you rephrase that?"

    def get_conversation_history(self, user_id):
        self._ensure_conversation_loaded(user_id)
        return self._conversations.get(user_id, [])

    def clear_conversation(self, user_id):
        self._conversations.pop(user_id, None)
        self._delete_conversation_from_store(user_id)

    def _ensure_conversation_loaded(self, user_id):
        if user_id not in self._conversations:
            stored = self._load_conversation_from_store(user_id)
            self._conversations[user_id] = stored

    def _conversation_collection(self):
        if db is None:
            return None
        return db.collection("conversations")

    def _load_conversation_from_store(self, user_id):
        col = self._conversation_collection()
        if col is None:
            return []
        try:
            doc = col.document(user_id).get()
            if doc.exists:
                data = doc.to_dict()
                messages = data.get("messages", [])
                cutoff = datetime.now(timezone.utc) - timedelta(
                    days=CONVERSATION_TTL_DAYS
                )
                valid = [
                    m for m in messages if m.get("timestamp", "") >= cutoff.isoformat()
                ]
                return valid
        except Exception as exc:
            logger.warning("Failed to load conversation for %s: %s", user_id, exc)
        return []

    def _persist_conversation(self, user_id, messages):
        col = self._conversation_collection()
        if col is None:
            return
        try:
            col.document(user_id).set(
                {
                    "messages": messages,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
        except Exception as exc:
            logger.warning("Failed to persist conversation for %s: %s", user_id, exc)

    def _delete_conversation_from_store(self, user_id):
        col = self._conversation_collection()
        if col is None:
            return
        try:
            col.document(user_id).delete()
        except Exception as exc:
            logger.warning("Failed to delete conversation for %s: %s", user_id, exc)

    def whats_if(self, user_id, current_data, scenario_changes, user_context):
        prompt = self._prompts.whats_if_analysis(
            current_data, scenario_changes, user_context
        )
        result = self._call_gemini(prompt, deterministic=True)
        if result:
            return result
        carbon_est = self._estimate_carbon(current_data)
        return {
            "estimated_impact": "positive",
            "carbon_saved": round(carbon_est * 0.15, 2),
            "comparison": "Estimated 15% reduction based on typical changes",
            "tip": "Every small change adds up. Try it for a week!",
        }

    def submit_feedback(self, user_id, feedback_type, user_message, user_context):
        prompt = self._prompts.feedback_prompt(
            user_message, feedback_type, user_context
        )
        result = self._call_gemini(prompt, deterministic=True)
        if result:
            self._cache.invalidate(user_id, "recommendations")
            return result
        return {
            "acknowledgment": "Thanks for your feedback!",
            "adjusted_tip": "Try reducing your carbon footprint by making small daily changes",
            "follow_up": "What area would you like to focus on?",
        }

    def invalidate_cache(self, user_id):
        self._cache.invalidate(user_id)

    def _estimate_carbon(self, data):
        return estimate_gemini_carbon(data)

    def _call_gemini(self, prompt, deterministic=False):
        if not self._api_key:
            logger.warning("Gemini API key not configured")
            return None

        url = f"{GEMINI_API_BASE}/{GEMINI_MODEL}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self._api_key,
        }
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.0 if deterministic else 0.3,
                "topP": 0.9,
                "maxOutputTokens": 512,
            },
        }
        if deterministic:
            payload["generationConfig"]["seed"] = 42

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=15,
                )
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_response(data)
                elif response.status_code == 429:
                    wait = RETRY_DELAY * (2**attempt)
                    logger.warning("Rate limited, retrying in %.1fs", wait)
                    time.sleep(wait)
                    continue
                else:
                    logger.error(
                        "Gemini API error %s: %s",
                        response.status_code,
                        response.text[:200],
                    )
                    return None
            except requests.RequestException as exc:
                last_error = exc
                logger.warning(
                    "Gemini request failed (attempt %d): %s", attempt + 1, exc
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)

        logger.error("Gemini call failed after %d retries: %s", MAX_RETRIES, last_error)
        return None

    def _parse_response(self, data):
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])
            return json.loads(text)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            logger.error("Failed to parse Gemini response: %s", exc)
            return None
