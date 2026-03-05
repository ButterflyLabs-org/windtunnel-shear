"""Human-readable console output formatter.

Produces compact, colored, scannable output like:

    → gpt-4o | 3 messages | 847 tokens
    ← 200 | 234 tokens | 1.2s | "The capital of France is..."
"""

from __future__ import annotations

import json
import sys
from typing import Any

from windtunnel_shear.core.models import InterceptedRequest, InterceptedResponse

# ANSI color codes
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


def _supports_color() -> bool:
    """Check if the terminal supports color output."""
    return hasattr(sys.stderr, "isatty") and sys.stderr.isatty()


def _truncate(text: str, max_len: int = 60) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _count_message_tokens(request: InterceptedRequest) -> str:
    """Rough token estimate from message content.

    Uses word count x 1.3 as a heuristic (English text averages ~1.3 tokens
    per word with BPE tokenizers). Falls back to char count / 4 for very
    short messages.
    """
    total_words = 0
    for m in request.messages:
        content = str(m.get("content", ""))
        if content:
            total_words += len(content.split())
    approx = max(total_words, 1) * 1.3
    # Add overhead for message framing (~4 tokens per message)
    approx += len(request.messages) * 4
    return f"~{int(approx)} tokens"


def _status_color(status_code: int) -> str:
    """Return ANSI color for an HTTP status code."""
    if 200 <= status_code < 300:
        return _GREEN
    if 400 <= status_code < 500:
        return _YELLOW
    if status_code >= 500:
        return _RED
    return _RESET


def format_request_line(request: InterceptedRequest, *, color: bool = True) -> str:
    """Format a request as a compact summary line.

    Args:
        request: The intercepted request.
        color: Whether to use ANSI colors.

    Returns:
        A formatted string like: → gpt-4o | 3 messages | ~212 tokens
    """
    parts: list[str] = []

    model = request.model or "unknown"
    msg_count = len(request.messages)
    token_est = _count_message_tokens(request)

    parts.append(model)
    parts.append(f"{msg_count} messages")
    if token_est:
        parts.append(token_est)
    if request.tools:
        parts.append(f"{len(request.tools)} tools")

    summary = " | ".join(parts)

    if color:
        return f"{_CYAN}{_BOLD}→{_RESET} {summary}"
    return f"→ {summary}"


def format_response_line(response: InterceptedResponse, *, color: bool = True) -> str:
    """Format a response as a compact summary line.

    Args:
        response: The intercepted response.
        color: Whether to use ANSI colors.

    Returns:
        A formatted string like: ← 200 | 234 tokens | 1.2s | "The capital..."
    """
    parts: list[str] = []

    status = str(response.status_code)
    total_tokens = response.usage.get("total_tokens")
    latency_s = response.latency_ms / 1000.0 if response.latency_ms else 0.0

    parts.append(status)
    if total_tokens is not None:
        parts.append(f"{total_tokens} tokens")
    if latency_s > 0:
        parts.append(f"{latency_s:.1f}s")

    # Content preview
    content = response.content
    if content:
        parts.append(f'"{_truncate(content)}"')
    elif response.has_tool_calls:
        tool_names = [tc.get("function", {}).get("name", "?") for tc in response.tool_calls]
        parts.append(f"tool_calls: {', '.join(tool_names)}")

    if response.is_shear_injected:
        parts.append(f"[shear: {response.reason}]")

    summary = " | ".join(parts)

    if color:
        sc = _status_color(response.status_code)
        return f"{sc}{_BOLD}←{_RESET} {summary}"
    return f"← {summary}"


def format_request_verbose(request: InterceptedRequest) -> str:
    """Format a request with full payload for --verbose mode.

    Args:
        request: The intercepted request.

    Returns:
        Full JSON representation of the request.
    """
    return json.dumps(request.raw, indent=2, ensure_ascii=False)


def format_response_verbose(response: InterceptedResponse) -> str:
    """Format a response with full payload for --verbose mode.

    Args:
        response: The intercepted response.

    Returns:
        Full JSON representation of the response.
    """
    return json.dumps(response.raw, indent=2, ensure_ascii=False)


def format_request_json(request: InterceptedRequest) -> str:
    """Format a request as machine-readable JSON for --json mode.

    Args:
        request: The intercepted request.

    Returns:
        Compact JSON line.
    """
    return json.dumps(
        {
            "direction": "request",
            "model": request.model,
            "messages": len(request.messages),
            "stream": request.stream,
            "tools": len(request.tools),
        },
        ensure_ascii=False,
    )


def format_response_json(response: InterceptedResponse) -> str:
    """Format a response as machine-readable JSON for --json mode.

    Args:
        response: The intercepted response.

    Returns:
        Compact JSON line.
    """
    data: dict[str, Any] = {
        "direction": "response",
        "status_code": response.status_code,
        "latency_ms": response.latency_ms,
        "usage": response.usage,
        "finish_reason": response.finish_reason,
    }
    if response.is_shear_injected:
        data["shear_reason"] = response.reason
    return json.dumps(data, ensure_ascii=False)


def format_jitter_diffs(request: InterceptedRequest, *, color: bool = True) -> str:
    """Format jitter diff lines for display.

    Args:
        request: The intercepted request (with jitter_log populated).
        color: Whether to use ANSI colors.

    Returns:
        Multi-line string with jitter diffs, or empty string if none.
    """
    if not request.jitter_log:
        return ""
    lines = []
    for entry in request.jitter_log:
        if color:
            lines.append(f"  {_YELLOW}jitter:{_RESET} {entry}")
        else:
            lines.append(f"  jitter: {entry}")
    return "\n".join(lines)


def log_exchange(
    request: InterceptedRequest,
    response: InterceptedResponse,
    *,
    verbose: bool = False,
    debug: bool = False,
    json_mode: bool = False,
    quiet: bool = False,
) -> None:
    """Log a request/response exchange to stderr.

    Args:
        request: The intercepted request.
        response: The intercepted response.
        verbose: Show enriched view with jitter diffs.
        debug: Show full JSON payloads.
        json_mode: Output machine-readable JSON.
        quiet: Suppress all output.
    """
    if quiet:
        return

    use_color = _supports_color() and not json_mode

    if json_mode:
        sys.stderr.write(format_request_json(request) + "\n")
        sys.stderr.write(format_response_json(response) + "\n")
    elif debug:
        sys.stderr.write(format_request_line(request, color=use_color) + "\n")
        jitter_diffs = format_jitter_diffs(request, color=use_color)
        if jitter_diffs:
            sys.stderr.write(jitter_diffs + "\n")
        sys.stderr.write(format_request_verbose(request) + "\n")
        sys.stderr.write(format_response_line(response, color=use_color) + "\n")
        sys.stderr.write(format_response_verbose(response) + "\n")
    elif verbose:
        sys.stderr.write(format_request_line(request, color=use_color) + "\n")
        jitter_diffs = format_jitter_diffs(request, color=use_color)
        if jitter_diffs:
            sys.stderr.write(jitter_diffs + "\n")
        sys.stderr.write(format_response_line(response, color=use_color) + "\n")
    else:
        sys.stderr.write(format_request_line(request, color=use_color) + "\n")
        sys.stderr.write(format_response_line(response, color=use_color) + "\n")
