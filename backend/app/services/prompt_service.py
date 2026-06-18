import json
import re
from typing import Any

from app.services.carbon_service import estimate_gemini_carbon as estimate_carbon


def sanitize_input(value: Any, max_length: int = 200) -> str:
    if not isinstance(value, str):
        value = str(value)
    value = value[:max_length]
    value = re.sub(r"[<>\n\r\t]", " ", value)
    value = re.sub(r"[{}[\]()]", "", value)
    return value.strip()


class PromptService:
    def recommendations(self, data):
        trend = data.get("score_trend", "stable")
        best = sanitize_input(data.get("best_category", "transport"))
        worst = sanitize_input(data.get("worst_category", "transport"))
        level = sanitize_input(data.get("level", "Beginner"))
        streak = data.get("streak", 0)

        focus_area = worst if trend in ("stable", "declining") else best
        focus_hint = (
            f"Focus on reducing {worst} (their highest impact area)"
            if focus_area == worst
            else f"Suggest ways to maintain their good habits in {best}"
        )

        prompt = f"""You are an AI sustainability coach. Generate 3 personalized carbon reduction recommendations based on this user data:
- Carbon score: {data.get("score", 0)}/100
- Transport: {sanitize_input(data.get("transport", "unknown"))}
- Food: {sanitize_input(data.get("food", "unknown"))}
- AC usage: {sanitize_input(data.get("ac_usage", "unknown"))}
- Level: {level}
- Streak: {streak} days
- Weekly average: {data.get("weekly_avg", 0)}
- Score trend: {trend}
- Best area: {best}
- Area to improve: {worst}

Rules:
- Each tip under 80 characters
- Focus on practical, college-student-friendly actions
- If user is Beginner, suggest simple entry-level actions
- If user has high streak or advanced level, suggest more impactful changes
- {focus_hint}
- Return ONLY valid JSON array of strings

Example:
["Tip one here", "Tip two here", "Tip three here"]"""
        return prompt

    def weekly_report(self, user_context):
        weekly_data = json.dumps(user_context.get("weekly_data", {}), default=str)
        prompt = f"""You are an AI sustainability analyst. Generate a weekly carbon report as JSON.

User context:
- Level: {sanitize_input(user_context.get("level", "Beginner"))}
- Streak: {user_context.get("streak", 0)} days
- Weekly average: {user_context.get("weekly_avg", 0)}
- Current score: {user_context.get("current_score", 0)}
- Activities logged: {user_context.get("activity_count", 0)}

Weekly data:
{weekly_data}

Return ONLY valid JSON with these exact keys:
{{
  "biggest_contributor": "category name",
  "best_improvement": "description",
  "next_week_goal": "achievable goal",
  "summary": "2-3 sentence motivational summary"
}}

Keep each field under 120 characters. Focus on data-driven insights."""
        return prompt

    def eco_personality(self, user_context):
        weekly_data = json.dumps(user_context.get("weekly_data", {}), default=str)
        prompt = f"""You are an AI sustainability analyst. Generate an eco-personality profile as JSON.

User data:
- Level: {sanitize_input(user_context.get("level", "Beginner"))}
- Streak: {user_context.get("streak", 0)} days
- Weekly average: {user_context.get("weekly_avg", 0)}

Breakdown:
{weekly_data}

Return ONLY valid JSON with these exact keys:
{{
  "personality": "creative title like Eco Explorer",
  "strength": "their lowest carbon category",
  "weakness": "their highest carbon category",
  "next_goal": "one specific reduction target"
}}

Keep each field under 80 characters."""
        return prompt

    def daily_mission(self, user_context):
        level = sanitize_input(user_context.get("level", "Beginner"))
        prompt = f"""You are an AI gamification designer. Generate ONE daily sustainability challenge for a {level} level college student.

Return ONLY valid JSON:
{{
  "challenge": "specific one-day task",
  "reward": 50
}}

Rules:
- Realistic for a college student
- Completable in one day
- Measurable outcome
- Reward between 30-100 based on difficulty
- challenge field under 100 characters"""
        return prompt

    def chat_response(self, user_message, user_context, conversation_history=None):
        history_text = ""
        if conversation_history:
            history_lines = []
            for msg in conversation_history[-6:]:
                role = msg.get("role", "user")
                content = sanitize_input(msg.get("content", ""), 500)
                if role == "system":
                    history_lines.append(f"[{content}]")
                else:
                    history_lines.append(f"{role}: {content}")
            history_text = "Recent conversation:\n" + "\n".join(history_lines) + "\n"

        trend = user_context.get("score_trend", "stable")
        best = user_context.get("best_category", "N/A")
        worst = user_context.get("worst_category", "N/A")
        level = sanitize_input(user_context.get("level", "Beginner"))
        streak = user_context.get("streak", 0)
        trend_note = ""
        if trend == "improving":
            trend_note = "The user is improving — keep them motivated and reinforce their good habits."
        elif trend == "declining":
            trend_note = "The user's scores have been declining — be encouraging and suggest small, easy wins."

        tone = "supportive and encouraging"
        if level == "Planet Hero" and streak > 20:
            tone = "concise and challenge-oriented, assume they know the basics"
        elif level == "Eco Warrior" and streak > 7:
            tone = "confident and action-oriented, suggest intermediate optimizations"

        context = f"""User context:
- Level: {level}
- Streak: {streak} days
- Weekly average carbon score: {user_context.get("weekly_avg", 0)}
- Current score: {user_context.get("current_score", 0)}
- Activities logged: {user_context.get("activity_count", 0)}
- Score trend: {trend}
- Best category: {best} (lowest carbon impact)
- Area to improve: {worst} (highest carbon impact)
"""

        prompt = f"""You are an AI sustainability coach named EcoMentor. You help users understand and reduce their carbon footprint.

{context}
{history_text}
Coaching tone: {tone}. {trend_note}
User message: {sanitize_input(user_message, 1000)}

Respond conversationally and helpfully. Keep responses under 150 words. Reference the user's trend and categories when relevant. If asked something outside sustainability, gently steer back. Return ONLY a JSON object with a single "response" field containing your reply."""

        return prompt

    def whats_if_analysis(self, current_data, scenario_changes, user_context):
        carbon_estimate = estimate_carbon(current_data)
        prompt = f"""You are an AI sustainability analyst. Analyze the impact of a lifestyle change on carbon footprint.

Current activity:
- Transport: {sanitize_input(current_data.get("transport", "unknown"))} for {current_data.get("distance", 0)} km
- Food: {sanitize_input(current_data.get("food_type", "unknown"))}
- AC usage: {sanitize_input(current_data.get("ac_usage", "unknown"))}
- Plastic waste: {current_data.get("plastic_waste", 0)} kg
- Estimated daily carbon: {carbon_estimate} kg CO2e

Proposed change:
- {sanitize_input(scenario_changes.get("description", "No change"), 300)}

User level: {sanitize_input(user_context.get("level", "Beginner"))}

Return ONLY valid JSON:
{{
  "estimated_impact": "positive or negative",
  "carbon_saved": 0.0,
  "comparison": "brief comparison to current (reference baseline: {carbon_estimate} kg CO2e)",
  "tip": "one practical suggestion"
}}

Use the baseline carbon estimate ({carbon_estimate} kg CO2e) to calculate realistic savings. Be conservative. Focus on realistic outcomes."""
        return prompt

    def feedback_prompt(self, user_message, feedback_type, user_context):
        prompt = f"""You are an AI sustainability coach. A user has provided feedback on a recommendation.

Feedback type: {sanitize_input(feedback_type, 50)}
User feedback: {sanitize_input(user_message, 500)}
User level: {sanitize_input(user_context.get("level", "Beginner"))}

Acknowledge their feedback and provide an adjusted or alternative recommendation.
Return ONLY valid JSON:
{{
  "acknowledgment": "brief acknowledgment",
  "adjusted_tip": "alternative recommendation based on feedback",
  "follow_up": "optional follow-up question"
}}

Keep each field under 120 characters."""
        return prompt
