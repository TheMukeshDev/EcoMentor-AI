import json
import logging
import os
import time
from datetime import datetime, timezone

import requests

from app.services.prompt_service import PromptService
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODEL = "gemini-2.0-flash"
MAX_RETRIES = 3
RETRY_DELAY = 1.0

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

    def chat(self, user_id, user_message, user_context):
        if user_id not in self._conversations:
            self._conversations[user_id] = []
        history = self._conversations[user_id]
        prompt = self._prompts.chat_response(user_message, user_context, history)
        result = self._call_gemini(prompt)
        if result and isinstance(result, dict) and "response" in result:
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
                    "content": result["response"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            if len(history) > 50:
                self._conversations[user_id] = history[-50:]
            return result["response"]
        return "I'm here to help with your sustainability questions. Could you rephrase that?"

    def get_conversation_history(self, user_id):
        return self._conversations.get(user_id, [])

    def clear_conversation(self, user_id):
        self._conversations.pop(user_id, None)

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
        transport = data.get("transport", "walking")
        distance = float(data.get("distance", 0))
        food_type = data.get("food_type", "vegetarian")
        ac_usage = data.get("ac_usage", "none")
        plastic_waste = float(data.get("plastic_waste", 0))

        transport_factor = {
            "walking": 0,
            "bicycle": 0,
            "bus": 0.089,
            "metro": 0.041,
            "car": 0.171,
            "plane": 0.255,
        }.get(transport, 0.089)
        food_factor = {"vegan": 1.5, "vegetarian": 1.7, "non_vegetarian": 2.5}.get(
            food_type, 1.7
        )
        ac_factor = {"none": 0, "1-2": 0.5, "3-5": 1.2, "6+": 2.0}.get(ac_usage, 0)

        return (
            transport_factor * distance + food_factor + ac_factor + plastic_waste * 0.5
        )

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
