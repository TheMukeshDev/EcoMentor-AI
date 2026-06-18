import json
import re


def sanitize_input(value, max_length=200):
    if not isinstance(value, str):
        value = str(value)
    value = value[:max_length]
    value = re.sub(r"[<>\n\r\t]", " ", value)
    value = re.sub(r"[{}[\]()]", "", value)
    return value.strip()


def estimate_carbon(data):
    transport = data.get("transport", "walking")
    distance = float(data.get("distance", 0))
    food_type = data.get("food_type", "vegetarian")
    ac_usage = data.get("ac_usage", "none")
    plastic_waste = float(data.get("plastic_waste", 0))
    transport_emissions = {
        "walking": 0,
        "bicycle": 0,
        "bus": 0.089,
        "metro": 0.041,
        "car": 0.171,
        "plane": 0.255,
    }.get(transport, 0.089) * distance
    food_emissions = {"vegan": 1.5, "vegetarian": 1.7, "non_vegetarian": 2.5}.get(
        food_type, 1.7
    )
    ac_emissions = {"none": 0, "1-2": 0.5, "3-5": 1.2, "6+": 2.0}.get(ac_usage, 0)
    waste_emissions = plastic_waste * 0.5
    return round(
        transport_emissions + food_emissions + ac_emissions + waste_emissions, 2
    )


class PromptService:
    def recommendations(self, data):
        prompt = f"""You are an AI sustainability coach. Generate 3 personalized carbon reduction recommendations based on this user data:
- Carbon score: {data.get("score", 0)}/100
- Transport: {sanitize_input(data.get("transport", "unknown"))}
- Food: {sanitize_input(data.get("food", "unknown"))}
- AC usage: {sanitize_input(data.get("ac_usage", "unknown"))}
- Level: {sanitize_input(data.get("level", "Beginner"))}
- Streak: {data.get("streak", 0)} days
- Weekly average: {data.get("weekly_avg", 0)}

Rules:
- Each tip under 80 characters
- Focus on practical, college-student-friendly actions
- If user is Beginner, suggest simple entry-level actions
- If user has high streak or advanced level, suggest more impactful changes
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
                history_lines.append(f"{role}: {content}")
            history_text = "Recent conversation:\n" + "\n".join(history_lines) + "\n"

        context = f"""User context:
- Level: {sanitize_input(user_context.get("level", "Beginner"))}
- Streak: {user_context.get("streak", 0)} days
- Weekly average carbon score: {user_context.get("weekly_avg", 0)}
- Current score: {user_context.get("current_score", 0)}
- Activities logged: {user_context.get("activity_count", 0)}
"""

        prompt = f"""You are an AI sustainability coach named EcoMentor. You help users understand and reduce their carbon footprint.

{context}
{history_text}
User message: {sanitize_input(user_message, 1000)}

Respond conversationally and helpfully. Keep responses under 150 words. If the user asks about their data, reference the context above. If asked something outside sustainability, gently steer back. Return ONLY a JSON object with a single "response" field containing your reply."""

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
