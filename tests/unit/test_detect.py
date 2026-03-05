"""Tests for provider auto-detection."""

from __future__ import annotations

from windtunnel_shear.providers.detect import detect_upstream


class TestDetectUpstream:
    def test_openai_key(self) -> None:
        assert detect_upstream("Bearer sk-abc123def456") == "https://api.openai.com/v1"

    def test_openai_key_no_bearer(self) -> None:
        assert detect_upstream("sk-abc123def456") == "https://api.openai.com/v1"

    def test_anthropic_key(self) -> None:
        assert detect_upstream("Bearer sk-ant-abc123") == "https://api.anthropic.com/v1"

    def test_anthropic_key_no_bearer(self) -> None:
        assert detect_upstream("sk-ant-xyz789") == "https://api.anthropic.com/v1"

    def test_unknown_key(self) -> None:
        assert detect_upstream("Bearer some-random-token") == ""

    def test_empty_header(self) -> None:
        assert detect_upstream("") == ""

    def test_bearer_only(self) -> None:
        assert detect_upstream("Bearer ") == ""

    def test_case_insensitive_bearer(self) -> None:
        assert detect_upstream("BEARER sk-test123") == "https://api.openai.com/v1"

    def test_whitespace_handling(self) -> None:
        assert detect_upstream("  Bearer   sk-test123  ") == "https://api.openai.com/v1"
