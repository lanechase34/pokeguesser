from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.test import TestCase

from config.middleware import RequestContextMiddleware, get_request_context


def _make_request(**meta: str) -> HttpRequest:
    request = HttpRequest()
    request.META.update(meta)
    return request


def _noop_response(request: HttpRequest) -> HttpResponse:
    return HttpResponse("ok")


class TestGetClientIp(TestCase):
    """Unit tests for _get_client_ip - the IP extraction priority chain."""

    def test_cloudflare_ip_takes_priority(self) -> None:
        request = _make_request(
            HTTP_CF_CONNECTING_IP="1.2.3.4",
            HTTP_X_FORWARDED_FOR="9.9.9.9",
            REMOTE_ADDR="127.0.0.1",
        )
        result = RequestContextMiddleware._get_client_ip(request)
        assert result == "1.2.3.4"

    def test_cloudflare_ip_strips_whitespace(self) -> None:
        request = _make_request(HTTP_CF_CONNECTING_IP="  1.2.3.4  ")
        assert RequestContextMiddleware._get_client_ip(request) == "1.2.3.4"

    def test_cloudflare_comma_list_returns_first(self) -> None:
        """CF header should return only the first IP when multiple present."""
        request = _make_request(HTTP_CF_CONNECTING_IP="1.2.3.4, 5.6.7.8")
        assert RequestContextMiddleware._get_client_ip(request) == "1.2.3.4"

    def test_x_forwarded_for_used_when_no_cf_header(self) -> None:
        request = _make_request(
            HTTP_X_FORWARDED_FOR="5.6.7.8, 10.0.0.1",
            REMOTE_ADDR="127.0.0.1",
        )
        assert RequestContextMiddleware._get_client_ip(request) == "5.6.7.8"

    def test_x_forwarded_for_strips_whitespace(self) -> None:
        request = _make_request(HTTP_X_FORWARDED_FOR="  5.6.7.8  ")
        assert RequestContextMiddleware._get_client_ip(request) == "5.6.7.8"

    def test_remote_addr_used_when_no_proxy_headers(self) -> None:
        request = _make_request(REMOTE_ADDR="192.168.1.1")
        assert RequestContextMiddleware._get_client_ip(request) == "192.168.1.1"

    def test_returns_none_when_no_ip_headers_present(self) -> None:
        request = HttpRequest()  # no META at all
        assert RequestContextMiddleware._get_client_ip(request) is None

    def test_old_http_cf_connecting_ip_header_is_not_used(self) -> None:
        """Regression: Django transforms header names - raw 'CF-Connecting-IP'
        must NOT be used; only 'HTTP_CF_CONNECTING_IP' is valid."""
        request = _make_request(
            **{"CF-Connecting-IP": "1.2.3.4"},  # wrong key - raw header name
            REMOTE_ADDR="9.9.9.9",
        )
        # Should fall through to REMOTE_ADDR because the raw key is not recognised
        assert RequestContextMiddleware._get_client_ip(request) == "9.9.9.9"


class TestRequestContextMiddleware(TestCase):
    """Integration tests for the full middleware __call__ cycle."""

    def _run(self, request: HttpRequest) -> HttpResponse:
        mw = RequestContextMiddleware(_noop_response)
        return mw(request)

    def test_ip_available_inside_request(self) -> None:
        captured: dict[str, str | None] = {}

        def get_response(req: HttpRequest) -> HttpResponse:
            captured.update(get_request_context())
            return HttpResponse("ok")

        request = _make_request(REMOTE_ADDR="10.0.0.1", HTTP_USER_AGENT="TestBot/1.0")
        RequestContextMiddleware(get_response)(request)

        assert captured["ip_address"] == "10.0.0.1"
        assert captured["user_agent"] == "TestBot/1.0"

    def test_context_cleared_after_request(self) -> None:
        request = _make_request(REMOTE_ADDR="10.0.0.1", HTTP_USER_AGENT="Bot")
        self._run(request)

        ctx = get_request_context()
        assert ctx["ip_address"] is None
        assert ctx["user_agent"] is None

    def test_context_cleared_even_when_view_raises(self) -> None:
        def boom(req: HttpRequest) -> HttpResponse:
            raise RuntimeError("view exploded")

        request = _make_request(REMOTE_ADDR="1.1.1.1")
        with self.assertRaises(RuntimeError):
            RequestContextMiddleware(boom)(request)

        ctx = get_request_context()
        assert ctx["ip_address"] is None
        assert ctx["user_agent"] is None

    def test_cloudflare_ip_stored_in_context(self) -> None:
        captured: dict[str, str | None] = {}

        def get_response(req: HttpRequest) -> HttpResponse:
            captured.update(get_request_context())
            return HttpResponse("ok")

        request = _make_request(
            HTTP_CF_CONNECTING_IP="203.0.113.5",
            REMOTE_ADDR="10.0.0.1",
            HTTP_USER_AGENT="CF-Bot",
        )
        RequestContextMiddleware(get_response)(request)

        assert captured["ip_address"] == "203.0.113.5"

    def test_user_agent_defaults_to_empty_string_when_missing(self) -> None:
        captured: dict[str, str | None] = {}

        def get_response(req: HttpRequest) -> HttpResponse:
            captured.update(get_request_context())
            return HttpResponse("ok")

        request = _make_request(REMOTE_ADDR="1.1.1.1")
        RequestContextMiddleware(get_response)(request)

        assert captured["user_agent"] == ""


class TestGetRequestContextOutsideRequest(TestCase):
    """get_request_context() must be safe to call outside a request cycle."""

    def test_returns_none_ip_outside_request(self) -> None:
        ctx = get_request_context()
        assert ctx["ip_address"] is None

    def test_returns_none_user_agent_outside_request(self) -> None:
        ctx = get_request_context()
        assert ctx["user_agent"] is None
