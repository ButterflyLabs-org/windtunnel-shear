"""Testing an agentic tool-calling loop.

Shear understands tool calls natively. Use it to test how your agent
handles failures in the tool-calling loop:

    # Combine latency with prompt noise
    shear proxy --fault latency:200ms --jitter noise:0.1

Shear's agent-aware accessors (is_tool_result, pending_tool_calls,
tool_call_count) let hooks make decisions based on the agentic context.
"""
