import pytest


class TestCarbonService:
    def test_calculate_default(self, carbon_service):
        score = carbon_service.calculate("walking", 0, "none", "vegan", 0)
        assert score == 0.5

    def test_calculate_car_transport(self, carbon_service):
        score = carbon_service.calculate("car", 10, "none", "vegan", 0)
        assert score == 10.5

    def test_calculate_plane(self, carbon_service):
        score = carbon_service.calculate("plane", 100, "none", "vegan", 0)
        assert score == 200.5

    def test_calculate_ac_heavy(self, carbon_service):
        score = carbon_service.calculate("walking", 0, "6+", "vegan", 0)
        assert score == 4.5

    def test_calculate_non_veg(self, carbon_service):
        score = carbon_service.calculate("walking", 0, "none", "non_vegetarian", 0)
        assert score == 3.0

    def test_calculate_with_waste(self, carbon_service):
        score = carbon_service.calculate("walking", 0, "none", "vegan", 1)
        assert score == 2.5

    def test_get_breakdown_structure(self, carbon_service):
        breakdown = carbon_service.get_breakdown("car", 10, "1-2", "vegetarian", 0.5)
        assert "total" in breakdown
        assert "transport" in breakdown
        assert "electricity" in breakdown
        assert "food" in breakdown
        assert "waste" in breakdown
        assert breakdown["transport"] == 10.0

    def test_calculate_unknown_transport_defaults(self, carbon_service):
        score = carbon_service.calculate("unknown_mode", 10, "none", "vegan", 0)
        assert score == 0.5

    def test_regional_factor_eu(self):
        from app.services.carbon_service import CarbonService

        svc = CarbonService(region="eu")
        score = svc.calculate("walking", 0, "1-2", "vegan", 0)
        assert score == pytest.approx(0.5 + 1.5 * 0.5 * 0.65, rel=0.01)

    def test_regional_factor_india(self):
        from app.services.carbon_service import CarbonService

        svc = CarbonService(region="india")
        score = svc.calculate("walking", 0, "1-2", "vegan", 0)
        assert score == pytest.approx(0.5 + 1.5 * 0.5 * 1.2, rel=0.01)

    def test_set_region(self, carbon_service):
        carbon_service.set_region("eu")
        assert carbon_service.region == "eu"

    def test_get_regions(self):
        from app.services.carbon_service import CarbonService

        regions = CarbonService.get_regions()
        assert "us" in regions
        assert "eu" in regions
        assert "global" in regions
