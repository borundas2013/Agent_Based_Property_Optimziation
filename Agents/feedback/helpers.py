from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .constants import (
    ISSUE_CHEMICAL_INVALID,
    ISSUE_GROUP1_MISSING,
    ISSUE_GROUP2_MISSING,
    ISSUE_PROPERTY_PREDICTION_FAILED,
    ISSUE_REACTION_INCOMPATIBLE,
    ISSUE_REQUESTED_GROUPS_FAILED,
)


def safe_float(x: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        return default


def determine_optimization_mode(
    property_result: Optional[Dict[str, Any]]
) -> Tuple[str, str]:
    if not property_result:
        return "joint", "none"

    dtg = safe_float(property_result.get("dtg"), 0.0) or 0.0
    der = safe_float(property_result.get("der"), 0.0) or 0.0
    tol_tg = safe_float(property_result.get("tol_tg"), 1.0) or 1.0
    tol_er = safe_float(property_result.get("tol_er"), 1.0) or 1.0

    tg_ratio = dtg / max(tol_tg, 1e-8)
    er_ratio = der / max(tol_er, 1e-8)

    if tg_ratio <= 1.0 and er_ratio <= 1.0:
        return "joint", "none"

    if tg_ratio > er_ratio * 1.25:
        return "tg_first", "tg"
    if er_ratio > tg_ratio * 1.25:
        return "er_first", "er"

    return "joint", "both"


def build_design_suggestions(
    property_result: Optional[Dict[str, Any]],
    group1: Optional[str],
    group2: Optional[str],
    issue_codes: List[str],
) -> List[str]:
    suggestions: List[str] = []

    pred_tg = safe_float(property_result.get("predicted_tg")) if property_result else None
    pred_er = safe_float(property_result.get("predicted_er")) if property_result else None
    target_tg = safe_float(property_result.get("tg_target")) if property_result else None
    target_er = safe_float(property_result.get("er_target")) if property_result else None

    tol_tg = safe_float(property_result.get("tol_tg"), 10.0) if property_result else 10.0
    tol_er = safe_float(property_result.get("tol_er"), 5.0) if property_result else 5.0
    tol_tg = tol_tg if tol_tg is not None else 10.0
    tol_er = tol_er if tol_er is not None else 5.0

    dtg: Optional[float] = None
    der: Optional[float] = None
    if pred_tg is not None and target_tg is not None:
        dtg = abs(pred_tg - target_tg)
    if pred_er is not None and target_er is not None:
        der = abs(pred_er - target_er)

    if ISSUE_CHEMICAL_INVALID in issue_codes:
        suggestions.append(
            "Regenerate chemically valid and plausible monomers with valid SMILES syntax and realistic bonding."
        )

    if ISSUE_REACTION_INCOMPATIBLE in issue_codes:
        suggestions.append(
            "Use a chemically compatible reactive pair that can form a thermoset network."
        )

    if ISSUE_REQUESTED_GROUPS_FAILED in issue_codes:
        suggestions.append(
            "Ensure the requested groups are present in the correct monomers and placed consistently with the prompt."
        )

    if ISSUE_GROUP1_MISSING in issue_codes and group1:
        suggestions.append(
            f"Ensure group1 '{group1}' is present in monomer1 with sufficient multiplicity for crosslinking."
        )

    if ISSUE_GROUP2_MISSING in issue_codes and group2:
        suggestions.append(
            f"Ensure group2 '{group2}' is present in monomer2 with sufficient multiplicity for crosslinking."
        )

    if ISSUE_CHEMICAL_INVALID not in issue_codes and ISSUE_PROPERTY_PREDICTION_FAILED not in issue_codes:
        if pred_tg is not None and target_tg is not None and dtg is not None:
            if dtg > tol_tg:
                if pred_tg < target_tg:
                    suggestions.append(
                        "Increase Tg by introducing more rigid, aromatic, cyclic, or polar motifs."
                    )
                elif pred_tg > target_tg:
                    suggestions.append(
                        "Decrease Tg by introducing more flexible aliphatic or ether-rich linkers."
                    )

        if pred_er is not None and target_er is not None and der is not None:
            if der > tol_er:
                if pred_er < target_er:
                    suggestions.append(
                        "Increase Er by increasing crosslink-supporting reactive site density or network rigidity."
                    )
                elif pred_er > target_er:
                    suggestions.append(
                        "Decrease Er by reducing excessive crosslink density or adding controlled flexibility while preserving reactivity."
                    )

    seen = set()
    deduped = []
    for suggestion in suggestions:
        if suggestion not in seen:
            deduped.append(suggestion)
            seen.add(suggestion)

    return deduped


def build_feedback_text(
    issue_messages: List[str],
    suggestions: List[str],
) -> str:
    if not issue_messages:
        return (
            "ISSUES DETECTED:\n"
            "- No critical issue detected. The monomers are valid, satisfy group/reactivity checks, "
            "and are within the requested property tolerances."
        )

    lines = ["ISSUES DETECTED:"]
    for message in issue_messages:
        lines.append(f"- {message}")

    if suggestions:
        lines.append("")
        lines.append("SUGGESTED REVISION ACTIONS:")
        for suggestion in suggestions:
            lines.append(f"- {suggestion}")

    return "\n".join(lines)
