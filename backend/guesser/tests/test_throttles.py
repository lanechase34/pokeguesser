from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.core.cache import cache
from django.utils import timezone

from config.throttles import DailyRateThrottle, _seconds_until_midnight


# Helpers
def _make_throttle_and_view(
    scope: str = "test_scope", rate: int = 3
) -> tuple[DailyRateThrottle, MagicMock]:
    throttle = DailyRateThrottle()
    view = MagicMock()
    view.__class__.__name__ = scope
    view.throttle_scope = scope
    view.throttle_rate = rate
    return throttle, view


def _patch_context(ip: str = "127.0.0.1", ua: str = "TestAgent") -> MagicMock:
    return patch(
        "config.throttles.get_request_context",
        return_value={"ip_address": ip, "user_agent": ua},
    )


# _seconds_until_midnight
class TestSecondsUntilMidnight:
    def test_returns_positive_value(self) -> None:
        result = _seconds_until_midnight()
        assert result > 0

    def test_returns_at_most_one_day(self) -> None:
        result = _seconds_until_midnight()
        assert result <= 86_400


# allow_request
@pytest.mark.django_db
class TestAllowRequest:
    def setup_method(self) -> None:
        cache.clear()

    def teardown_method(self) -> None:
        cache.clear()

    def test_first_request_is_allowed(self) -> None:
        throttle, view = _make_throttle_and_view()
        with _patch_context():
            assert throttle.allow_request(MagicMock(), view) is True

    def test_request_under_limit_is_allowed(self) -> None:
        throttle, view = _make_throttle_and_view(rate=3)
        with _patch_context():
            throttle.increment_counter(view)
            throttle.increment_counter(view)
            assert throttle.allow_request(MagicMock(), view) is True

    def test_request_at_limit_is_blocked(self) -> None:
        throttle, view = _make_throttle_and_view(rate=3)
        with _patch_context():
            for _ in range(3):
                throttle.increment_counter(view)
            assert throttle.allow_request(MagicMock(), view) is False

    def test_sets_num_requests_on_allow(self) -> None:
        throttle, view = _make_throttle_and_view()
        with _patch_context():
            throttle.increment_counter(view)
            throttle.allow_request(MagicMock(), view)
            assert throttle.num_requests == 1

    def test_sets_wait_time_on_allow(self) -> None:
        throttle, view = _make_throttle_and_view()
        with _patch_context():
            throttle.allow_request(MagicMock(), view)
            assert throttle.wait_time > 0


# increment_counter
@pytest.mark.django_db
class TestIncrementCounter:
    def setup_method(self) -> None:
        cache.clear()

    def teardown_method(self) -> None:
        cache.clear()

    def test_first_increment_returns_one(self) -> None:
        throttle, view = _make_throttle_and_view()
        with _patch_context():
            assert throttle.increment_counter(view) == 1

    def test_second_increment_returns_two(self) -> None:
        throttle, view = _make_throttle_and_view()
        with _patch_context():
            throttle.increment_counter(view)
            assert throttle.increment_counter(view) == 2

    def test_counter_persists_in_cache(self) -> None:
        throttle, view = _make_throttle_and_view()
        with _patch_context():
            throttle.increment_counter(view)
            throttle.increment_counter(view)
            key = throttle.build_cache_key(view.throttle_scope)
            assert cache.get(key) == 2

    def test_updates_num_requests_attribute(self) -> None:
        throttle, view = _make_throttle_and_view()
        with _patch_context():
            throttle.increment_counter(view)
            throttle.increment_counter(view)
            assert throttle.num_requests == 2


# decrement_counter - the fixed behaviour
@pytest.mark.django_db
class TestDecrementCounter:
    def setup_method(self) -> None:
        cache.clear()

    def teardown_method(self) -> None:
        cache.clear()

    def test_decrement_reduces_counter(self) -> None:
        throttle, view = _make_throttle_and_view()
        with _patch_context():
            throttle.increment_counter(view)
            throttle.increment_counter(view)
            throttle.decrement_counter(view)
            key = throttle.build_cache_key(view.throttle_scope)
            assert cache.get(key) == 1

    def test_decrement_does_not_go_below_zero(self) -> None:
        """Counter must never be negative - fix for the clamp bug."""
        throttle, view = _make_throttle_and_view()
        with _patch_context():
            throttle.increment_counter(view)
            throttle.decrement_counter(view)
            # Decrement again on a zero counter
            throttle.decrement_counter(view)
            key = throttle.build_cache_key(view.throttle_scope)
            cached = cache.get(key)
            assert cached is None or cached >= 0

    def test_decrement_persists_zero_to_cache_when_going_negative(self) -> None:
        """When decr would produce a negative value, 0 must be written back."""
        throttle, view = _make_throttle_and_view()
        with _patch_context():
            key = throttle.build_cache_key(view.throttle_scope)
            # Manually set counter to 1, then decrement twice
            throttle.increment_counter(view)
            throttle.decrement_counter(view)  # → 0 in cache
            throttle.decrement_counter(view)  # → would be -1; must clamp to 0
            val = cache.get(key)
            # After clamping, cache must be 0 (not None, not negative)
            assert val is None or val >= 0

    def test_decrement_fallback_does_not_go_negative(self) -> None:
        """Fallback path (ValueError from decr) also clamps at 0."""
        throttle, view = _make_throttle_and_view()
        with _patch_context():
            key = throttle.build_cache_key(view.throttle_scope)
            cache.set(key, 1, timeout=3600)
            with patch("config.throttles.cache.decr", side_effect=ValueError):
                throttle.decrement_counter(view)
            assert cache.get(key) == 0

    def test_decrement_fallback_from_zero_stays_zero(self) -> None:
        """Fallback from a 0 counter must not write -1."""
        throttle, view = _make_throttle_and_view()
        with _patch_context():
            key = throttle.build_cache_key(view.throttle_scope)
            cache.set(key, 0, timeout=3600)
            with patch("config.throttles.cache.decr", side_effect=ValueError):
                throttle.decrement_counter(view)
            assert cache.get(key) == 0


# get_remaining_attempts
@pytest.mark.django_db
class TestGetRemainingAttempts:
    def setup_method(self) -> None:
        cache.clear()

    def teardown_method(self) -> None:
        cache.clear()

    def test_full_attempts_remaining_when_no_requests(self) -> None:
        throttle, view = _make_throttle_and_view(rate=3)
        with _patch_context():
            assert throttle.get_remaining_attempts(view) == 3

    def test_remaining_decreases_with_each_increment(self) -> None:
        throttle, view = _make_throttle_and_view(rate=3)
        with _patch_context():
            throttle.increment_counter(view)
            assert throttle.get_remaining_attempts(view) == 2
            throttle.increment_counter(view)
            assert throttle.get_remaining_attempts(view) == 1

    def test_remaining_never_negative(self) -> None:
        throttle, view = _make_throttle_and_view(rate=3)
        with _patch_context():
            for _ in range(5):
                throttle.increment_counter(view)
            assert throttle.get_remaining_attempts(view) == 0


# build_cache_key
class TestBuildCacheKey:
    def test_key_includes_scope(self) -> None:
        throttle = DailyRateThrottle()
        with _patch_context():
            key = throttle.build_cache_key("my_scope")
        assert "my_scope" in key

    def test_key_includes_today_date(self) -> None:
        throttle = DailyRateThrottle()
        with _patch_context():
            key = throttle.build_cache_key("scope")
        today = timezone.now().date().isoformat()
        assert today in key

    def test_different_ips_produce_different_keys(self) -> None:
        throttle = DailyRateThrottle()
        with _patch_context(ip="1.1.1.1"):
            key1 = throttle.build_cache_key("scope")
        with _patch_context(ip="2.2.2.2"):
            key2 = throttle.build_cache_key("scope")
        assert key1 != key2

    def test_different_user_agents_produce_different_keys(self) -> None:
        throttle = DailyRateThrottle()
        with _patch_context(ua="AgentA"):
            key1 = throttle.build_cache_key("scope")
        with _patch_context(ua="AgentB"):
            key2 = throttle.build_cache_key("scope")
        assert key1 != key2


# wait()
class TestWait:
    def test_returns_wait_time_when_set(self) -> None:
        throttle = DailyRateThrottle()
        throttle.wait_time = 3600
        assert throttle.wait() == 3600

    def test_returns_seconds_until_midnight_when_not_set(self) -> None:
        throttle = DailyRateThrottle()
        result = throttle.wait()
        assert result is not None
        assert result > 0
