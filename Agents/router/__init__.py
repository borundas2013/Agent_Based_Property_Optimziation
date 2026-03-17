"""
Router module package.

This package contains the refactored logic from `Agents/Router.py`.
"""

from typing import Any, Dict, Optional

__all__ = ["evaluate"]


def evaluate(
    input_json_path: str = "Evaluations/prompts/property_prompt_sample_100.json",
    max_iterations: int = 3,
) -> Optional[Dict[str, Any]]:
    # Lazy import to avoid importing LLM clients at package import time.
    from .evaluate import evaluate as _evaluate

    return _evaluate(input_json_path=input_json_path, max_iterations=max_iterations)

