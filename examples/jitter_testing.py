"""Prompt jitter testing examples.

Test how robust your LLM is to input perturbations:

    # Inject typos into 10% of characters
    shear proxy --jitter noise:0.1

    # Contradict the system prompt
    shear proxy --jitter contradict

    # Pad with 5 irrelevant conversation turns
    shear proxy --jitter dilute:5

    # Rephrase the system prompt
    shear proxy --jitter rephrase
"""
