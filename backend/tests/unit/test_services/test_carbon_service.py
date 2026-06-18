from app.services.carbon_service import CarbonService


class TestCarbonService:
    def setup_method(self):
        self.service = CarbonService()

    def test_calculate_minimal_activity(self):
        result = self.service.calculate("walking", 0, "none", "vegan", 0)
        assert result == 0.5

    def test_calculate_car_commute(self):
        result = self.service.calculate("car", 20, "1-2", "non_vegetarian", 0.5)
        assert result > 0

    def test_calculate_plane_high_impact(self):
        result = self.service.calculate("plane", 1000, "none", "non_vegetarian", 0)
        assert result > 2000

    def test_get_breakdown_returns_all_categories(self):
        breakdown = self.service.get_breakdown("car", 50, "3-5", "vegetarian", 1)
        assert "total" in breakdown
        assert "transport" in breakdown
        assert "electricity" in breakdown
        assert "food" in breakdown
        assert "waste" in breakdown

    def test_get_breakdown_sums_to_total(self):
        breakdown = self.service.get_breakdown("bus", 10, "1-2", "vegan", 0.2)
        expected = (
            breakdown["transport"]
            + breakdown["electricity"]
            + breakdown["food"]
            + breakdown["waste"]
        )
        assert breakdown["total"] == round(expected, 2)

    def test_calculate_with_defaults(self):
        result = self.service.calculate("walking", 0, "none", "vegetarian", 0)
        assert result > 0

    def test_invalid_transport_defaults_to_zero(self):
        result = self.service.calculate("unknown", 100, "none", "vegan", 0)
        assert result >= 0

    def test_calculate_bicycle_same_as_walking(self):
        walk = self.service.calculate("bicycle", 10, "none", "vegan", 0)
        bike = self.service.calculate("bicycle", 10, "none", "vegan", 0)
        assert walk == bike

    def test_plastic_waste_scales_linearly(self):
        low_waste = self.service.calculate("walking", 0, "none", "vegan", 1)
        high_waste = self.service.calculate("walking", 0, "none", "vegan", 5)
        waste_diff = high_waste - low_waste
        assert waste_diff == 8.0
