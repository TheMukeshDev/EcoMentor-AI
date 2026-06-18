import json


class PromptService:
    def recommendations(self, data):
        prompt = f"""You are an AI sustainability coach. Generate 3 personalized carbon reduction recommendations based on this user data:
- Carbon score: {data.get("score", 0)}/100
- Transport: {data.get("transport", "unknown")}
- Food: {data.get("food", "unknown")}
- AC usage: {data.get("ac_usage", "unknown")}

Rules:
- Each tip under 80 characters
- Focus on practical, college-student-friendly actions
- Return ONLY valid JSON array of strings

Example:
["Tip one here", "Tip two here", "Tip three here"]"""
        return prompt

    def weekly_report(self, user_context):
        weekly_data = json.dumps(user_context.get("weekly_data", {}), default=str)
        prompt = f"""You are an AI sustainability analyst. Generate a weekly carbon report as JSON.

User context:
- Level: {user_context.get("level", "Beginner")}
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
- Level: {user_context.get("level", "Beginner")}
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
        level = user_context.get("level", "Beginner")
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
