"""Tests for providers layer: exceptions, response, retry_config, base."""

from __future__ import annotations

import pytest

from providers.base import BaseProvider
from providers.exceptions import (
    ERROR_CODES,
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderError,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderServerError,
    ProviderTimeoutError,
    ProviderValidationError,
)
from providers.response import (
    ProviderResponse,
    error_response,
    success_response,
)
from providers.retry_config import (
    RetryConfig,
    get_retry_after,
    is_retryable_error,
)

# ── Concrete provider for testing BaseProvider ──────────────────────────


class MockProvider(BaseProvider[bool]):
    async def health_check(self):  # type: ignore[override]
        return self._create_response(True, True)

    async def close(self) -> None:
        pass


# ── Exceptions ──────────────────────────────────────────────────────────


class TestProviderError:
    def test_basic_error(self):
        err = ProviderError("test message")
        assert str(err) == "test message"
        assert err.provider is None
        assert err.error_code is None
        assert err.original_error is None

    def test_with_provider_and_code(self):
        err = ProviderError("msg", provider="telegram", error_code="CODE_123")
        assert "msg" in str(err)
        assert "provider=telegram" in str(err)
        assert "code=CODE_123" in str(err)

    def test_with_original_error(self):
        original = ValueError("cause")
        err = ProviderError("msg", original_error=original)
        assert err.original_error is original

    def test_str_without_optional_fields(self):
        err = ProviderError("hello")
        assert str(err) == "hello"


class TestProviderSubclasses:
    def test_connection_error(self):
        err = ProviderConnectionError("conn failed", provider="db")
        assert isinstance(err, ProviderError)
        assert "conn failed" in str(err)

    def test_timeout_error(self):
        err = ProviderTimeoutError("timeout")
        assert isinstance(err, ProviderError)

    def test_auth_error(self):
        err = ProviderAuthenticationError("bad token")
        assert isinstance(err, ProviderError)

    def test_not_found_error(self):
        err = ProviderNotFoundError("missing")
        assert isinstance(err, ProviderError)

    def test_validation_error(self):
        err = ProviderValidationError("bad input")
        assert isinstance(err, ProviderError)

    def test_server_error(self):
        err = ProviderServerError("500")
        assert isinstance(err, ProviderError)

    def test_rate_limit_error_basic(self):
        err = ProviderRateLimitError("too many", provider="api")
        assert isinstance(err, ProviderError)
        assert err.retry_after is None

    def test_rate_limit_error_with_retry(self):
        err = ProviderRateLimitError(
            "too many",
            provider="api",
            retry_after=30,
            error_code="RATE_LIMIT",
        )
        assert err.retry_after == 30
        assert err.error_code == "RATE_LIMIT"

    def test_rate_limit_error_with_original(self):
        original = ValueError("orig")
        err = ProviderRateLimitError("msg", original_error=original)
        assert err.original_error is original


class TestErrorCodes:
    def test_has_all_expected_codes(self):
        expected = {
            "CONNECTION_REFUSED",
            "TIMEOUT",
            "RATE_LIMIT",
            "AUTH_FAILED",
            "NOT_FOUND",
            "VALIDATION",
            "SERVER_ERROR",
            "UNKNOWN",
        }
        assert set(ERROR_CODES.keys()) == expected

    def test_values_are_non_empty(self):
        for code in ERROR_CODES.values():
            assert code and len(code) > 0


# ── Response ────────────────────────────────────────────────────────────


class TestProviderResponse:
    def test_success_response(self):
        resp = ProviderResponse(data="hello", success=True, provider="test")
        assert resp.is_success
        assert not resp.is_error
        assert resp.data == "hello"

    def test_error_response(self):
        resp = ProviderResponse(data=None, success=False, provider="test", error_message="fail", error_code="ERR")
        assert resp.is_error
        assert not resp.is_success
        assert resp.error_message == "fail"

    def test_default_values(self):
        resp = ProviderResponse(data=42, success=True, provider="p")
        assert resp.error_message is None
        assert resp.error_code is None
        assert resp.metadata == {}

    def test_metadata(self):
        resp = ProviderResponse(data=1, success=True, provider="p", metadata={"key": "val"})
        assert resp.metadata["key"] == "val"

    def test_get_data_success(self):
        resp = ProviderResponse(data="ok", success=True, provider="p")
        assert resp.get_data() == "ok"

    def test_get_data_error_raises(self):
        resp = ProviderResponse(data=None, success=False, provider="p", error_message="bad")
        with pytest.raises(ValueError):
            resp.get_data()

    def test_get_data_none_data_raises(self):
        resp = ProviderResponse(data=None, success=True, provider="p")
        with pytest.raises(ValueError):
            resp.get_data()

    def test_get_or_default_success(self):
        resp = ProviderResponse(data="ok", success=True, provider="p")
        assert resp.get_or_default("default") == "ok"

    def test_get_or_default_error_returns_default(self):
        resp = ProviderResponse(data=None, success=False, provider="p")
        assert resp.get_or_default("default") == "default"

    def test_get_or_default_none_data_returns_default(self):
        resp = ProviderResponse(data=None, success=True, provider="p")
        assert resp.get_or_default("default") == "default"

    def test_map_success(self):
        resp = ProviderResponse(data=5, success=True, provider="p")
        mapped = resp.map(lambda x: x * 2)
        assert mapped.is_success
        assert mapped.data == 10

    def test_map_error_preserves_error(self):
        resp = ProviderResponse(data=None, success=False, provider="p", error_message="fail")
        mapped = resp.map(lambda x: x)
        assert mapped.is_error
        assert mapped.error_message == "fail"

    def test_map_exception_returns_error(self):
        resp = ProviderResponse(data="hello", success=True, provider="p")
        mapped = resp.map(lambda x: 1 / 0)  # type: ignore[arg-type]
        assert mapped.is_error
        assert mapped.error_code == "TRANSFORM_ERROR"
        assert "Transform error" in (mapped.error_message or "")


class TestResponseHelpers:
    def test_success_response_creates_correct_object(self):
        resp = success_response(data="test", provider="api")
        assert resp.is_success
        assert resp.data == "test"
        assert resp.provider == "api"

    def test_success_response_with_metadata(self):
        resp = success_response(data="x", provider="api", metadata={"ts": 123})
        assert resp.metadata["ts"] == 123

    def test_error_response_creates_correct_object(self):
        resp = error_response(error_message="fail", provider="api")
        assert resp.is_error
        assert resp.error_message == "fail"
        assert resp.error_code == "UNKNOWN_ERROR"

    def test_error_response_with_code(self):
        resp = error_response(error_message="fail", provider="api", error_code="E123")
        assert resp.error_code == "E123"

    def test_error_response_empty_metadata(self):
        resp = error_response(error_message="fail", provider="api")
        assert resp.metadata == {}


# ── RetryConfig ─────────────────────────────────────────────────────────


class TestRetryConfig:
    def test_default_returns_dict(self):
        result = RetryConfig.default()
        assert isinstance(result, dict)
        assert "stop" in result
        assert "wait" in result
        assert "retry" in result
        assert result["reraise"] is True

    def test_default_with_custom_params(self):
        result = RetryConfig.default(max_attempts=5, min_wait=2, max_wait=20)
        assert isinstance(result, dict)

    def test_aggressive_returns_dict(self):
        result = RetryConfig.aggressive()
        assert isinstance(result, dict)
        assert "stop" in result
        assert "wait" in result
        assert result["reraise"] is True

    def test_no_retry_returns_dict(self):
        result = RetryConfig.no_retry()
        assert isinstance(result, dict)
        assert "stop" in result
        assert result["reraise"] is True

    def test_for_rate_limit_returns_dict(self):
        result = RetryConfig.for_rate_limit()
        assert isinstance(result, dict)
        assert "retry" in result
        assert result["reraise"] is True

    def test_is_retryable_error_connection(self):
        assert is_retryable_error(ProviderConnectionError("x"))

    def test_is_retryable_error_timeout(self):
        assert is_retryable_error(ProviderTimeoutError("x"))

    def test_is_retryable_error_server(self):
        assert is_retryable_error(ProviderServerError("x"))

    def test_is_not_retryable_auth(self):
        assert not is_retryable_error(ProviderAuthenticationError("x"))

    def test_is_not_retryable_validation(self):
        assert not is_retryable_error(ProviderValidationError("x"))

    def test_is_not_retryable_not_found(self):
        assert not is_retryable_error(ProviderNotFoundError("x"))

    def test_is_not_retryable_generic(self):
        assert not is_retryable_error(ValueError("generic"))

    def test_get_retry_after_rate_limit(self):
        err = ProviderRateLimitError("msg", retry_after=42)
        assert get_retry_after(err) == 42

    def test_get_retry_after_none(self):
        err = ProviderRateLimitError("msg")
        assert get_retry_after(err) is None

    def test_get_retry_after_non_rate_limit(self):
        assert get_retry_after(ValueError("x")) is None


# ── BaseProvider ────────────────────────────────────────────────────────


class TestBaseProvider:
    def test_name_property(self):
        provider = MockProvider("test-provider")
        assert provider.name == "test-provider"

    def test_stats_initial(self):
        provider = MockProvider("p")
        assert provider.stats == {"requests": 0, "errors": 0}

    def test_track_request(self):
        provider = MockProvider("p")
        provider._track_request()
        provider._track_request()
        assert provider.stats["requests"] == 2
        assert provider.stats["errors"] == 0

    def test_track_error(self):
        provider = MockProvider("p")
        provider._track_error()
        provider._track_error()
        provider._track_error()
        assert provider.stats["requests"] == 0
        assert provider.stats["errors"] == 3

    def test_track_both(self):
        provider = MockProvider("p")
        provider._track_request()
        provider._track_request()
        provider._track_error()
        assert provider.stats == {"requests": 2, "errors": 1}

    def test_create_response_success(self):
        provider = MockProvider("my-provider")
        resp = provider._create_response(data=True, success=True)
        assert resp.is_success
        assert resp.data is True
        assert resp.provider == "my-provider"

    def test_create_response_error(self):
        provider = MockProvider("my-provider")
        resp = provider._create_response(data=None, success=False, error_message="fail", error_code="E1")
        assert resp.is_error
        assert resp.error_message == "fail"
        assert resp.error_code == "E1"

    def test_create_response_with_metadata(self):
        provider = MockProvider("p")
        resp = provider._create_response(data=1, success=True, metadata={"key": "v"})
        assert resp.metadata["key"] == "v"

    @pytest.mark.asyncio
    async def test_health_check(self):
        provider = MockProvider("p")
        resp = await provider.health_check()
        assert resp.is_success
        assert resp.data is True

    @pytest.mark.asyncio
    async def test_close(self):
        provider = MockProvider("p")
        await provider.close()  # should not raise
