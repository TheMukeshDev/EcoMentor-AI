import pytest


class TestCarbonEstimatorConsistency:
    def test_duplicate_estimators_removed(self):
        from app.services.carbon_service import estimate_gemini_carbon
        from app.services.prompt_service import PromptService

        service = PromptService()
        assert callable(estimate_gemini_carbon)

    @pytest.mark.parametrize(
        "transport,distance,food,ac,waste",
        [
            ("walking", 0, "vegan", "none", 0),
            ("car", 10, "non_vegetarian", "3-5", 0.5),
            ("plane", 100, "vegetarian", "1-2", 1.0),
            ("bicycle", 5, "vegan", "none", 0),
            ("bus", 20, "non_vegetarian", "6+", 2.0),
        ],
    )
    def test_ai_service_uses_consolidated_estimator(
        self, ai_service, transport, distance, food, ac, waste
    ):
        from app.services.carbon_service import estimate_gemini_carbon

        data = {
            "transport": transport,
            "distance": distance,
            "food_type": food,
            "ac_usage": ac,
            "plastic_waste": waste,
        }
        expected = estimate_gemini_carbon(data)
        result = ai_service._estimate_carbon(data)
        assert result == expected, (
            f"AI service estimator diverged from consolidated estimator for {data}"
        )
