import json
import logging
import os
import time

import requests

from app.services.prompt_service import PromptService
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODEL = "gemini-2.0-flash"
MAX_RETRIES = 3
RETRY_DELAY = 1.0


class AIService:
    def __init__(self, api_key=None, ai_report_repository=None):
        self._api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._prompts = PromptService()
        self._cache = CacheService(ai_report_repository)

    def get_recommendations(self, user_id, data):
        cached = self._cache.get(user_id, "recommendations")
        if cached:
            return cached

        prompt = self._prompts.recommendations(data)
        result = self._call_gemini(prompt)
        if result:
            self._cache.set(user_id, "recommendations", result)
        return result

    def get_weekly_report(self, user_id, user_context):
        cached = self._cache.get(user_id, "weekly_report")
        if cached:
            return cached

        prompt = self._prompts.weekly_report(user_context)
        result = self._call_gemini(prompt)
        if result:
            self._cache.set(user_id, "weekly_report", result)
        return result

    def get_eco_personality(self, user_id, user_context):
        cached = self._cache.get(user_id, "eco_personality")
        if cached:
            return cached

        prompt = self._prompts.eco_personality(user_context)
        result = self._call_gemini(prompt)
        if result:
            self._cache.set(user_id, "eco_personality", result)
        return result

    def get_daily_mission(self, user_id, user_context):
        cached = self._cache.get(user_id, "daily_mission")
        if cached:
            return cached

        prompt = self._prompts.daily_mission(user_context)
        result = self._call_gemini(prompt)
        if result:
            self._cache.set(user_id, "daily_mission", result)
        return result

    def _call_gemini(self, prompt):
        if not self._api_key:
            logger.warning("Gemini API key not configured")
            return None

        url = f"{GEMINI_API_BASE}/{GEMINI_MODEL}:generateContent"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "topP": 0.9,
                "maxOutputTokens": 512,
            },
        }

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    params={"key": self._api_key},
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
