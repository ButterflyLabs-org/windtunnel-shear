"""Infrastructure fault testing examples.

Test how your application handles LLM API failures:

    # 30% of requests get rate-limited
    shear proxy --fault rate-limit:0.3

    # Add 500ms latency to every response
    shear proxy --fault latency:500ms

    # 10% of requests return 503
    shear proxy --fault error:503:0.1

    # Timeout after 10 seconds
    shear proxy --fault timeout:10s
"""
