"""Tests for intent classifier."""

import pytest
from app.utils.intent_classifier import (
    classify_intent,
    get_faq_answer,
    get_emission_lookup,
)


class TestClassifyIntent:
    """Tests for intent classification."""

    def test_static_faq_carbon_footprint(self):
        """Should classify 'what is carbon footprint' as static_faq."""
        assert classify_intent("What is a carbon footprint?") == "static_faq"

    def test_static_faq_net_zero(self):
        """Should classify 'what is net zero' as static_faq."""
        assert classify_intent("What is net zero?") == "static_faq"

    def test_emission_lookup(self):
        """Should classify emission queries as emission_lookup."""
        assert classify_intent("How much CO2 does beef produce?") == "emission_lookup"

    def test_personal_query(self):
        """Should classify personal queries as personal."""
        assert classify_intent("Show me my report") == "personal"
        assert classify_intent("my carbon footprint") == "personal"

    def test_general_query(self):
        """Should classify general queries as general."""
        assert classify_intent("Tell me about recycling") == "general"

    def test_empty_message(self):
        """Should classify empty message as general."""
        assert classify_intent("") == "general"
        assert classify_intent("   ") == "general"


class TestGetFaqAnswer:
    """Tests for FAQ answer retrieval."""

    def test_returns_answer_for_known_question(self):
        """Should return answer for known FAQ."""
        answer = get_faq_answer("What is a carbon footprint?")
        assert answer is not None
        assert "CO₂" in answer

    def test_returns_none_for_unknown_question(self):
        """Should return None for non-FAQ questions."""
        answer = get_faq_answer("What is the meaning of life?")
        assert answer is None


class TestGetEmissionLookup:
    """Tests for emission factor lookups."""

    def test_lookup_beef(self):
        """Should return beef emission factor."""
        result = get_emission_lookup("How much CO2 does beef produce?")
        assert result is not None
        assert result["item"] == "beef"
        assert result["factor_kg_co2e"] == 27.0

    def test_lookup_car(self):
        """Should return car emission factor."""
        result = get_emission_lookup("How much CO2 does a car produce?")
        assert result is not None
        assert result["item"] == "car"

    def test_lookup_unknown_item(self):
        """Should return None for unknown items."""
        result = get_emission_lookup("How much CO2 does a spaceship produce?")
        assert result is None

    def test_no_match_pattern(self):
        """Should return None for non-matching queries."""
        result = get_emission_lookup("Tell me about trees")
        assert result is None
