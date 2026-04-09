from __future__ import annotations

from typing import Any, Dict, Optional


def build_final_result(
    monomer1: str,
    monomer2: str,
    reason: str,
    property_prediction: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "monomer1": monomer1,
        "monomer2": monomer2,
        "reason": reason,
    }
    if property_prediction:
        out["predicted_tg"] = property_prediction.get("predicted_tg")
        out["predicted_er"] = property_prediction.get("predicted_er")
        out["dtg"] = property_prediction.get("dtg")
        out["der"] = property_prediction.get("der")
        out["ratio_1"] = property_prediction.get("ratio_1")
        out["ratio_2"] = property_prediction.get("ratio_2")
        out["within_property_tolerance"] = property_prediction.get(
            "within_property_tolerance"
        )
    else:
        out["predicted_tg"] = None
        out["predicted_er"] = None
    return out


def compact_sample_for_save(sample: Dict[str, Any]) -> Dict[str, Any]:
    prop = sample.get("property_prediction_full") or {}
    notes = sample.get("threshold_notes") or {}
    return {
        "monomer1": sample["monomer1"],
        "monomer2": sample["monomer2"],
        "reason": sample.get("reason", ""),
        "predicted_tg": prop.get("predicted_tg"),
        "predicted_er": prop.get("predicted_er"),
        "dtg": prop.get("dtg"),
        "der": prop.get("der"),
        "ratio_1": prop.get("ratio_1"),
        "ratio_2": prop.get("ratio_2"),
        "within_property_tolerance": prop.get("within_property_tolerance"),
        "suggest_follow_up_agent": bool(notes.get("suggest_follow_up_agent", False)),
    }


def build_slim_run_payload(
    initial_sample: Dict[str, Any],
    best_sample: Dict[str, Any],
    target_tg: Optional[float],
    target_er: Optional[float],
    group1: Optional[str],
    group2: Optional[str],
) -> Dict[str, Any]:
    return {
        "meta": {
            "target_tg": target_tg,
            "target_er": target_er,
            "group1": group1,
            "group2": group2,
        },
        "initial": compact_sample_for_save(initial_sample),
        "best": compact_sample_for_save(best_sample),
    }
