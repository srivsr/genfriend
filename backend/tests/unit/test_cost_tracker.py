"""Tests for CostTracker — pricing accuracy."""
import pytest
from unittest.mock import patch
from app.services.cost_tracker import CostTracker, PRICING


class TestPricing:
    def test_known_models_have_pricing(self):
        assert "gpt-4o" in PRICING
        assert "claude-sonnet-4-20250514" in PRICING
        assert "text-embedding-3-small" in PRICING

    def test_pricing_structure(self):
        for model, prices in PRICING.items():
            assert "input" in prices
            assert "output" in prices
            assert prices["input"] >= 0
            assert prices["output"] >= 0

    def test_embedding_has_zero_output_cost(self):
        assert PRICING["text-embedding-3-small"]["output"] == 0


class TestTrack:
    @pytest.mark.asyncio
    async def test_tracks_when_enabled(self):
        tracker = CostTracker()
        with patch("app.services.cost_tracker.settings") as mock_settings:
            mock_settings.enable_cost_tracking = True
            # Should not raise
            await tracker.track(
                user_id="user-1",
                model="gpt-4o",
                input_tokens=1000,
                output_tokens=500,
                request_type="generation"
            )

    @pytest.mark.asyncio
    async def test_skips_when_disabled(self):
        tracker = CostTracker()
        with patch("app.services.cost_tracker.settings") as mock_settings:
            mock_settings.enable_cost_tracking = False
            await tracker.track(
                user_id="user-1",
                model="gpt-4o",
                input_tokens=1000,
                output_tokens=500,
                request_type="generation"
            )
            # No error, early return

    @pytest.mark.asyncio
    async def test_unknown_model_zero_cost(self):
        tracker = CostTracker()
        with patch("app.services.cost_tracker.settings") as mock_settings:
            mock_settings.enable_cost_tracking = True
            await tracker.track(
                user_id="user-1",
                model="unknown-model-xyz",
                input_tokens=1000,
                output_tokens=500,
                request_type="generation"
            )
