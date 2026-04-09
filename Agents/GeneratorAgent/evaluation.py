from __future__ import annotations

import paths  # noqa: F401
from typing import Any, Dict, Optional, Tuple

from feedback.feedback import (
    ISSUE_CHEMICAL_INVALID,
    ISSUE_GROUP1_MISSING,
    ISSUE_GROUP2_MISSING,
    ISSUE_PROPERTY_PREDICTION_FAILED,
    ISSUE_REACTION_INCOMPATIBLE,
    ISSUE_REQUESTED_GROUPS_FAILED,
    check_property,
    generate_feedback,
)

from constants import STRUCTURAL_ISSUE_CODES


def safe_float(x: Any, default: float = 1e9) -> float:
    try:
        return float(x)
    except Exception:
        return default


def threshold_notes(
    feedback_dict: Dict[str, Any],
    property_full: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    codes = set(feedback_dict.get("issue_codes", []))
    prop = feedback_dict.get("property_details") or property_full or {}
    within_tg = prop.get("within_tg_tolerance")
    within_er = prop.get("within_er_tolerance")
    within_both = prop.get("within_property_tolerance")
    if property_full:
        if within_tg is None:
            within_tg = property_full.get("within_tg_tolerance")
        if within_er is None:
            within_er = property_full.get("within_er_tolerance")
        if within_both is None:
            within_both = property_full.get("within_property_tolerance")

    structural_ok = len(codes & STRUCTURAL_ISSUE_CODES) == 0
    pred_ok = ISSUE_PROPERTY_PREDICTION_FAILED not in codes
    tg_ok = bool(within_tg) if within_tg is not None else None
    er_ok = bool(within_er) if within_er is not None else None
    both_ok = bool(within_both) if within_both is not None else None

    needs_follow_up = (
        (not structural_ok)
        or (not pred_ok)
        or (both_ok is False)
    )
    parts = []
    if not structural_ok:
        parts.append(
            "Structural gates failed (chemical validity, reaction compatibility, "
            "and/or requested group placement); use a chemistry/structure revision agent."
        )
    elif not pred_ok:
        parts.append(
            "Property prediction failed; follow-up may be needed once structures are valid."
        )
    elif both_ok is False:
        parts.append(
            "Tg and/or Er error is above tolerance; consider a property-focused refinement agent."
        )
    else:
        parts.append(
            "Structural checks pass and property errors are within tolerance; "
            "no follow-up agent required for these criteria."
        )

    return {
        "chemical_validity_ok": ISSUE_CHEMICAL_INVALID not in codes,
        "reaction_compatibility_ok": ISSUE_REACTION_INCOMPATIBLE not in codes,
        "group_consistency_ok": not (
            ISSUE_REQUESTED_GROUPS_FAILED in codes
            or ISSUE_GROUP1_MISSING in codes
            or ISSUE_GROUP2_MISSING in codes
        ),
        "structural_gates_all_passed": structural_ok,
        "property_prediction_ok": pred_ok,
        "tg_error_below_threshold": tg_ok,
        "er_error_below_threshold": er_ok,
        "both_property_errors_below_threshold": both_ok,
        "issue_codes": list(codes),
        "suggest_follow_up_agent": needs_follow_up,
        "follow_up_note": " ".join(parts),
    }


def rank_tuple(sample: Dict[str, Any]) -> Tuple[float, ...]:
    """
    Lower tuple is better. Priority:
    1) No structural issues
    2) Property prediction available
    3) Both Tg and Er errors within tolerance
    4) Minimize total error (dtg + der), then dtg, then der
    """
    fb = sample["feedback"]
    codes = set(fb.get("issue_codes", []))
    structural = codes & STRUCTURAL_ISSUE_CODES
    if structural:
        prop = fb.get("property_details") or sample.get("property_prediction_full") or {}
        dtg = safe_float(prop.get("dtg"), 1e9)
        der = safe_float(prop.get("der"), 1e9)
        return (
            4.0,
            float(len(structural)),
            dtg + der,
            dtg,
            der,
        )

    if ISSUE_PROPERTY_PREDICTION_FAILED in codes:
        return (3.0, 0.0, 0.0, 1e9, 1e9)

    prop = fb.get("property_details") or sample.get("property_prediction_full") or {}
    dtg = safe_float(prop.get("dtg"), 1e9)
    der = safe_float(prop.get("der"), 1e9)
    within = bool(prop.get("within_property_tolerance", False))

    if within:
        return (0.0, dtg + der, dtg, der, 0.0)
    return (1.0, dtg + der, dtg, der, 0.0)


def final_property_prediction(
    monomer_1: str,
    monomer_2: str,
    target_tg: Optional[float],
    target_er: Optional[float],
) -> Optional[Dict[str, Any]]:
    if target_tg is None or target_er is None:
        return None
    return check_property(
        monomer_1=monomer_1,
        monomer_2=monomer_2,
        target_tg=float(target_tg),
        target_er=float(target_er),
    )


def evaluate_sample(
    label: str,
    llm_result: Dict[str, str],
    target_tg: Optional[float],
    target_er: Optional[float],
    group1: Optional[str],
    group2: Optional[str],
    precomputed_feedback: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    m1 = llm_result["monomer1"]
    m2 = llm_result["monomer2"]
    if precomputed_feedback is not None:
        fb = precomputed_feedback
    else:
        fb = generate_feedback(
            monomer_1=m1,
            monomer_2=m2,
            group1=group1,
            group2=group2,
            target_tg=target_tg,
            target_er=target_er,
        )
    if ISSUE_CHEMICAL_INVALID in fb.get("issue_codes", []):
        prop = None
    else:
        prop = fb.get("property_details")
        if prop is None and target_tg is not None and target_er is not None:
            prop = final_property_prediction(m1, m2, target_tg, target_er)
    notes = threshold_notes(fb, prop)
    return {
        "label": label,
        "monomer1": m1,
        "monomer2": m2,
        "reason": llm_result.get("reason", ""),
        "feedback": fb,
        "property_prediction_full": prop,
        "threshold_notes": notes,
    }
