from __future__ import annotations

import json
import os
import re
from typing import Any, Dict


def to_jsonable(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, bool, int)):
        return obj
    if isinstance(obj, float):
        return obj
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(x) for x in obj]
    if hasattr(obj, "item"):
        try:
            return to_jsonable(obj.item())
        except Exception:
            pass
    try:
        return float(obj)
    except Exception:
        return str(obj)


def save_run_to_json(
    payload: Dict[str, Any],
    path: str,
) -> str:
    path = os.path.abspath(path)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(to_jsonable(payload), f, indent=2, ensure_ascii=False)
    return path


def parse_monomer_json(content: str) -> Dict[str, str]:
    if not content or not str(content).strip():
        raise ValueError("Empty model response")

    text = str(content).strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, count=1, flags=re.IGNORECASE)
        text = re.sub(r"\s*```\s*$", "", text, count=1)
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse model JSON. Raw response:\n{text}") from e

    for key in ("monomer1", "monomer2", "reason"):
        if key not in data:
            raise KeyError(f"Missing key {key!r} in parsed JSON")

    return {
        "monomer1": str(data["monomer1"]).strip(),
        "monomer2": str(data["monomer2"]).strip(),
        "reason": str(data["reason"]).strip(),
    }
