import hashlib
from datetime import timedelta
from typing import Any, Optional

from django.core.cache import cache
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.throttling import BaseThrottle
from rest_framework.views import APIView

from config.middleware import get_request_context


def _seconds_until_midnight() -> int:
    """Calculate seconds remaining until midnight."""
    now = timezone.now()
    tomorrow = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return int((tomorrow - now).total_seconds())


class DailyRateThrottle(BaseThrottle):
    """
    Throttles requests per day based on IP + User Agent.

    IMPORTANT: Only increments the counter for VALID requests.
    It checks the cache but doesn't increment until after validation passes.

    Usage in views:
        class MyView(APIView):
            throttle_classes = [DailyRateThrottle]
            throttle_scope = 'my_endpoint'  # Required: unique identifier
            throttle_rate = 3  # Optional: defaults to 3 requests per day
    """

    # Type hints for instance attributes set in allow_request
    num_requests: int
    wait_time: int

    def get_rate_limit(self, view: APIView) -> int:
        """
        Get the rate limit from the view, default to 5.
        """
        return getattr(view, "throttle_rate", 5)

    def get_scope(self, view: APIView) -> str:
        """
        Get the throttle scope from the view.
        """
        scope: Optional[str] = getattr(view, "throttle_scope", None)
        if not scope:
            # Fallback to view class name if no scope is defined
            scope = view.__class__.__name__
        return scope

    def build_cache_key(self, scope: str) -> str:
        """
        Build a unique cache key based on IP, User Agent, date, and scope.
        """
        context = get_request_context()
        ip = context["ip_address"]
        ua = context["user_agent"]
        raw = f"{ip}:{ua}"
        digest = hashlib.sha256(raw.encode()).hexdigest()
        today = timezone.now().date().isoformat()
        return f"rate:{scope}:{today}:{digest}"

    def allow_request(self, request: Request, view: APIView) -> bool:
        """
        Determine if the request should be allowed.

        """
        scope = self.get_scope(view)
        limit = self.get_rate_limit(view)
        cache_key = self.build_cache_key(scope)
        ttl = _seconds_until_midnight()

        count: Optional[Any] = cache.get(cache_key)

        if count is None:
            # First request of the day - allow it
            self.num_requests = 0
            self.wait_time = ttl
            return True

        if count >= limit:
            # Limit exceeded
            self.num_requests = count
            self.wait_time = ttl
            return False

        # Under limit - allow the request
        self.num_requests = count
        self.wait_time = ttl
        return True

    def increment_counter(self, view: APIView) -> int:
        """
        Manually increment the counter after validation passes.

        Call this in your view AFTER validating the request.

        Returns:
            int: The new count after incrementing
        """
        scope = self.get_scope(view)
        cache_key = self.build_cache_key(scope)
        ttl = _seconds_until_midnight()

        count = cache.get(cache_key)

        if count is None:
            # First request of the day
            cache.set(cache_key, 1, timeout=ttl)
            self.num_requests = 1
            return 1

        # Increment the counter
        try:
            count = cache.incr(cache_key)
        except ValueError:
            # Fallback for cache backends without incr
            count += 1
            cache.set(cache_key, count, timeout=ttl)

        self.num_requests = count
        return count

    def wait(self) -> Optional[int]:
        """
        Return the time (in seconds) until the throttle resets.
        """
        if hasattr(self, "wait_time"):
            return self.wait_time
        return _seconds_until_midnight()

    def get_attempts(self, view: APIView) -> int:
        """
        Get the current number of attempts made.

        Args:
            view: The view instance to get the scope from

        Returns:
            int: Current number of attempts (0 if no attempts yet)
        """
        scope = self.get_scope(view)
        cache_key = self.build_cache_key(scope)
        count: Optional[Any] = cache.get(cache_key)
        return count if count is not None else 0

    def get_remaining_attempts(self, view: APIView) -> int:
        """
        Get the number of remaining attempts.

        Args:
            view: The view instance to get the scope and limit from

        Returns:
            int: Number of remaining attempts (0 if limit exceeded)
        """
        attempts = self.get_attempts(view)
        limit = self.get_rate_limit(view)
        remaining = limit - attempts
        return max(0, remaining)
