"""Context dilution jitter."""

from __future__ import annotations

from windtunnel_shear.core.models import InterceptedRequest

_FILLER_PAIRS = [
    (
        {"role": "user", "content": "What's the weather like today?"},
        {"role": "assistant", "content": "I don't have access to weather data."},
    ),
    (
        {"role": "user", "content": "Tell me a fun fact."},
        {"role": "assistant", "content": "Honey never spoils."},
    ),
    (
        {"role": "user", "content": "What time is it?"},
        {
            "role": "assistant",
            "content": "I don't have access to the current time.",
        },
    ),
    (
        {"role": "user", "content": "How are you doing?"},
        {
            "role": "assistant",
            "content": "I'm doing well, thanks for asking!",
        },
    ),
    (
        {"role": "user", "content": "Can you count to five?"},
        {"role": "assistant", "content": "1, 2, 3, 4, 5."},
    ),
]


def apply_dilute(request: InterceptedRequest, count: int) -> InterceptedRequest:
    """Pad the conversation with irrelevant turns.

    Inserts filler user/assistant pairs before the last user message
    to test context window handling and attention.

    Args:
        request: The request to modify.
        count: Number of irrelevant turn pairs to insert.

    Returns:
        The modified request with diluted context.
    """
    if count <= 0:
        return request

    messages = request.messages

    insert_idx = 0
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "user":
            insert_idx = i
            break

    filler: list[dict[str, str]] = []
    for i in range(count):
        pair = _FILLER_PAIRS[i % len(_FILLER_PAIRS)]
        filler.append(dict(pair[0]))
        filler.append(dict(pair[1]))

    for j, msg in enumerate(filler):
        messages.insert(insert_idx + j, msg)

    return request
