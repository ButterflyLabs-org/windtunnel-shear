"""Custom hook examples.

Hooks let you intercept and modify LLM traffic programmatically.

Usage:
    shear proxy --hooks examples/custom_hooks.py
"""

from __future__ import annotations

# from windtunnel_shear import Hook
# from windtunnel_shear.core.models import InterceptedRequest, InterceptedResponse
#
# @Hook.before_request(name="add_system_prompt")
# def add_system_prompt(req: InterceptedRequest) -> InterceptedRequest:
#     req.messages.insert(0, {"role": "system", "content": "Always be concise."})
#     return req
#
# @Hook.after_response(name="log_tokens")
# def log_tokens(req: InterceptedRequest, resp: InterceptedResponse) -> InterceptedResponse:
#     print(f"Tokens used: {resp.usage.get('total_tokens', 'unknown')}")
#     return resp
