import threading
from django.http import HttpRequest, HttpResponse
from typing import Callable

# Thread-local storage, each request thread gets its own isolated copy
_request_context = threading.local()


def get_request_context() -> dict[str, str | None]:
    """
    Retrieve the current request context from thread-local storage.
    Returns empty dict if called outside of a request (e.g. cron, management command).
    """
    return {
        "ip_address": getattr(_request_context, "ip_address", None),
        "user_agent": getattr(_request_context, "user_agent", None),
    }


class RequestContextMiddleware:
    """
    Extracts the following request context values and stores it in thread-local storage:
    IP Address
    User Agent
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Store context BEFORE the request is processed
        _request_context.ip_address = self._get_client_ip(request)
        _request_context.user_agent = request.META.get("HTTP_USER_AGENT", "")

        try:
            response = self.get_response(request)
        finally:
            # Clean up AFTER the request is done
            # Important: prevents context from leaking to the next request on this thread
            _request_context.ip_address = None
            _request_context.user_agent = None

        return response

    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str | None:
        cloudflare_ip: str | None = request.META.get("CF-Connecting-IP")
        if cloudflare_ip:
            return cloudflare_ip.split(",")[0].strip()

        x_forwarded_for: str | None = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")
