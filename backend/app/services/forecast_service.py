"""Carbon Forecast service.

Uses linear regression on the user's last 60 days of data to predict
future emissions. Implements manual least-squares (no sklearn needed).
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from app.schemas.ai_schemas import ForecastResponse

logger = logging.getLogger(__name__)

# Default personal target: 20% below global average
GLOBAL_AVG_WEEKLY_KG = 90.4
DEFAULT_TARGET_WEEKLY_KG = round(GLOBAL_AVG_WEEKLY_KG * 0.8, 2)


class ForecastService:
    """Forecasts future carbon emissions using linear regression.

    Args:
        carbon_history_repo: Repository for carbon history data.
        user_repo: Repository for user profile data.
    """

    def __init__(
        self,
        carbon_history_repo: Any,
        user_repo: Any,
    ) -> None:
        self._carbon_history_repo = carbon_history_repo
        self._user_repo = user_repo

    def get_forecast(
        self, user_id: str, days: int = 30
    ) -> dict[str, Any]:
        """Generate a carbon emission forecast for the user.

        Args:
            user_id: The authenticated user's ID.
            days: Number of days to forecast (default 30).

        Returns:
            Validated forecast response dict.
        """
        days = max(7, min(days, 90))
        history = self._get_history(user_id)

        if len(history) < 3:
            return self._insufficient_data_response(days)

        scores = [e.get("carbon_score", 0) for e in history]
        slope, intercept = self._linear_regression(scores)
        predicted = self._predict(slope, intercept, len(scores), days)
        confidence = self._confidence_interval(scores, predicted)
        trend = self._determine_trend(slope)
        user = self._user_repo.get(user_id) or {}
        target = self._personal_target(user, days)
        top_lever = self._identify_top_lever(history)

        result = {
            "forecast_days": days,
            "predicted_total_kg": round(predicted, 2),
            "vs_personal_target_kg": round(predicted - target, 2),
            "trend": trend,
            "confidence_low": confidence[0],
            "confidence_high": confidence[1],
            "top_lever": top_lever,
        }

        return self._validate_response(result) or result

    def _get_history(
        self, user_id: str
    ) -> list[dict[str, Any]]:
        """Fetch the last 60 days of carbon history.

        Args:
            user_id: The user's ID.

        Returns:
            List of carbon history entries sorted by date.
        """
        today = datetime.now(timezone.utc)
        start = (today - timedelta(days=60)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")

        return self._carbon_history_repo.find_by_user_and_date_range(
            user_id, start, end
        )

    def _linear_regression(
        self, values: list[float]
    ) -> tuple[float, float]:
        """Compute least-squares linear regression.

        Args:
            values: List of daily carbon scores.

        Returns:
            Tuple of (slope, intercept).
        """
        n = len(values)
        if n == 0:
            return 0.0, 0.0

        x_vals = list(range(n))
        x_mean = sum(x_vals) / n
        y_mean = sum(values) / n

        numerator = sum(
            (x - x_mean) * (y - y_mean)
            for x, y in zip(x_vals, values)
        )
        denominator = sum((x - x_mean) ** 2 for x in x_vals)

        if denominator == 0:
            return 0.0, y_mean

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        return round(slope, 6), round(intercept, 4)

    def _predict(
        self,
        slope: float,
        intercept: float,
        current_len: int,
        days: int,
    ) -> float:
        """Predict total emissions over the forecast period.

        Args:
            slope: Regression slope.
            intercept: Regression intercept.
            current_len: Number of historical data points.
            days: Number of forecast days.

        Returns:
            Predicted total CO2e in kg.
        """
        total = 0.0
        for day in range(days):
            x = current_len + day
            daily = max(slope * x + intercept, 0)
            total += daily
        return round(total, 2)

    def _confidence_interval(
        self, values: list[float], predicted: float
    ) -> tuple[float, float]:
        """Calculate a simple confidence interval.

        Args:
            values: Historical score values.
            predicted: Predicted total.

        Returns:
            Tuple of (low_bound, high_bound).
        """
        if len(values) < 2:
            return (round(predicted * 0.8, 2), round(predicted * 1.2, 2))

        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance)

        margin = std_dev * 1.96 * math.sqrt(len(values))
        low = round(max(predicted - margin, 0), 2)
        high = round(predicted + margin, 2)
        return (low, high)

    def _determine_trend(
        self, slope: float
    ) -> Literal["improving", "stable", "worsening"]:
        """Classify the emission trend from regression slope.

        Args:
            slope: The regression slope value.

        Returns:
            One of 'improving', 'stable', or 'worsening'.
        """
        if slope < -0.05:
            return "improving"
        if slope > 0.05:
            return "worsening"
        return "stable"

    def _personal_target(
        self, user: dict[str, Any], days: int
    ) -> float:
        """Calculate the user's personal emission target.

        Args:
            user: User profile dict.
            days: Number of forecast days.

        Returns:
            Target total CO2e in kg for the period.
        """
        daily_target = DEFAULT_TARGET_WEEKLY_KG / 7
        return round(daily_target * days, 2)

    def _identify_top_lever(
        self, history: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Identify the single highest-impact reduction lever.

        Args:
            history: List of carbon history entries.

        Returns:
            Dict with action description and projected saving.
        """
        category_totals: dict[str, float] = {}
        for entry in history:
            for cat in ("transport", "electricity", "food", "waste"):
                category_totals[cat] = (
                    category_totals.get(cat, 0) + entry.get(cat, 0)
                )

        if not category_totals:
            return {
                "action": "Start logging activities to identify your top lever",
                "projected_saving_kg": 0.0,
            }

        worst = max(category_totals, key=lambda k: category_totals[k])
        saving = round(category_totals[worst] * 0.2, 2)

        actions = {
            "transport": f"Reduce car trips by 20% to save ~{saving} kg CO2e",
            "electricity": f"Cut electricity use by 20% to save ~{saving} kg CO2e",
            "food": f"Reduce meat meals by 20% to save ~{saving} kg CO2e",
            "waste": f"Reduce plastic waste by 20% to save ~{saving} kg CO2e",
        }

        return {
            "action": actions.get(worst, f"Reduce {worst} by 20%"),
            "projected_saving_kg": saving,
        }

    def _validate_response(
        self, result: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Validate the forecast result against the schema.

        Args:
            result: Forecast result dict.

        Returns:
            Validated dict or None if validation fails.
        """
        try:
            validated = ForecastResponse(**result)
            return validated.model_dump()
        except Exception as exc:
            logger.warning("Forecast validation failed: %s", exc)
            return None

    def _insufficient_data_response(
        self, days: int
    ) -> dict[str, Any]:
        """Return a response when there isn't enough data.

        Args:
            days: Requested forecast days.

        Returns:
            Fallback forecast dict with default values.
        """
        daily_avg = GLOBAL_AVG_WEEKLY_KG / 7
        predicted = round(daily_avg * days, 2)
        target = round(DEFAULT_TARGET_WEEKLY_KG / 7 * days, 2)

        return {
            "forecast_days": days,
            "predicted_total_kg": predicted,
            "vs_personal_target_kg": round(predicted - target, 2),
            "trend": "stable",
            "confidence_low": round(predicted * 0.7, 2),
            "confidence_high": round(predicted * 1.3, 2),
            "top_lever": {
                "action": "Log at least 3 days of activities to enable accurate forecasting",
                "projected_saving_kg": 0.0,
            },
        }
