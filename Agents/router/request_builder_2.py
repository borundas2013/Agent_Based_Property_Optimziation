# from typing import Any, Dict, List, Optional

# from router.scoring import decide_optimization_mode

# def build_property_revision_request(
#     result: Dict[str, Any],
#     default_tol_tg: float = 10.0,
#     default_tol_er: float = 10.0,
#     weight_tg: float = 0.5,
#     weight_er: float = 0.5,
# ) -> Dict[str, Any]:
#     """
#     Build the first revision request from the current best candidate.
#     This is the request used by the main reviser.
#     """

#     def _to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
#         try:
#             if value is None:
#                 return default
#             return float(value)
#         except (TypeError, ValueError):
#             return default

#     def _safe_div(num: float, den: float) -> float:
#         den = den if abs(den) > 1e-12 else 1e-12
#         return num / den

#     def _status(
#         pred: Optional[float], target: Optional[float], tol: Optional[float]
#     ) -> str:
#         if pred is None or target is None or tol is None:
#             return "unknown"
#         if pred > target + tol:
#             return "too_high"
#         if pred < target - tol:
#             return "too_low"
#         return "matched"

#     def _severity(norm_error: float) -> str:
#         if norm_error <= 1.0:
#             return "within_tolerance"
#         if norm_error <= 1.5:
#             return "moderate"
#         if norm_error <= 2.5:
#             return "high"
#         return "very_high"

#     property_details = result.get("property_details", {}) or {}

#     prompt = result.get("prompt", "")
#     monomer_1 = result.get("monomer_1", "")
#     monomer_2 = result.get("monomer_2", "")

#     target_tg = _to_float(result.get("target_tg"), _to_float(property_details.get("tg_target")))
#     target_er = _to_float(result.get("target_er"), _to_float(property_details.get("er_target")))

#     predicted_tg = _to_float(property_details.get("predicted_tg"))
#     predicted_er = _to_float(property_details.get("predicted_er"))

#     tol_tg = _to_float(property_details.get("tol_tg"), default_tol_tg)
#     tol_er = _to_float(property_details.get("tol_er"), default_tol_er)

#     dtg = _to_float(property_details.get("dtg"))
#     der = _to_float(property_details.get("der"))

#     tg_status = _status(predicted_tg, target_tg, tol_tg)
#     er_status = _status(predicted_er, target_er, tol_er)

#     normalized_dtg = _safe_div(
#         dtg if dtg is not None else 0.0, tol_tg if tol_tg is not None else default_tol_tg
#     )
#     normalized_der = _safe_div(
#         der if der is not None else 0.0, tol_er if tol_er is not None else default_tol_er
#     )

#     combined_score = (weight_tg * normalized_dtg) + (weight_er * normalized_der)

#     optimization_mode = decide_optimization_mode(result)

#     tg_needs_revision = dtg is not None and tol_tg is not None and dtg > tol_tg
#     er_needs_revision = der is not None and tol_er is not None and der > tol_er
#     needs_property_revision = bool(
#         tg_needs_revision or er_needs_revision or result.get("is_agent_call_needed", False)
#     )

#     if tg_needs_revision and er_needs_revision:
#         if normalized_dtg > normalized_der:
#             priority_property = "tg"
#         elif normalized_der > normalized_dtg:
#             priority_property = "er"
#         else:
#             priority_property = "joint"
#     elif tg_needs_revision:
#         priority_property = "tg"
#     elif er_needs_revision:
#         priority_property = "er"
#     else:
#         priority_property = "none"

#     recommended_actions: List[str] = []

#     if tg_status == "too_high":
#         recommended_actions.append("reduce predicted Tg")
#     elif tg_status == "too_low":
#         recommended_actions.append("increase predicted Tg")

#     if er_status == "too_high":
#         recommended_actions.append("reduce predicted Er")
#     elif er_status == "too_low":
#         recommended_actions.append("increase predicted Er")

#     if not recommended_actions:
#         recommended_actions.append("preserve current property alignment")

#     summary_parts: List[str] = []

#     if tg_status != "unknown":
#         summary_parts.append(
#             f"Predicted Tg is {predicted_tg} while target Tg is {target_tg} "
#             f"(error={dtg}, tolerance={tol_tg}, status={tg_status})."
#         )

#     if er_status != "unknown":
#         summary_parts.append(
#             f"Predicted Er is {predicted_er} while target Er is {target_er} "
#             f"(error={der}, tolerance={tol_er}, status={er_status})."
#         )

#     if priority_property == "tg":
#         summary_parts.append("Revision should focus primarily on Tg correction.")
#     elif priority_property == "er":
#         summary_parts.append("Revision should focus primarily on Er correction.")
#     elif priority_property == "joint":
#         summary_parts.append("Revision should jointly optimize Tg and Er.")
#     else:
#         summary_parts.append("Property values are within tolerance; revision is optional.")

#     summary = " ".join(summary_parts)

#     revision_goal_parts: List[str] = []

#     if tg_status == "too_high":
#         revision_goal_parts.append("lower predicted Tg")
#     elif tg_status == "too_low":
#         revision_goal_parts.append("raise predicted Tg")

#     if er_status == "too_high":
#         revision_goal_parts.append("lower predicted Er")
#     elif er_status == "too_low":
#         revision_goal_parts.append("raise predicted Er")

#     if revision_goal_parts:
#         revision_goal = "Revise the monomer pair to " + " and ".join(revision_goal_parts) + "."
#     else:
#         revision_goal = (
#             "Preserve the current monomer pair because property targets are already satisfied."
#         )

#     return {
#         "needs_property_revision": needs_property_revision,
#         "property_status": {
#             "tg": tg_status,
#             "er": er_status,
#         },
#         "severity": {
#             "tg": _severity(normalized_dtg),
#             "er": _severity(normalized_der),
#         },
#         "priority_property": priority_property,
#         "scores": {
#             "normalized_dtg": round(normalized_dtg, 6),
#             "normalized_der": round(normalized_der, 6),
#             "combined_score": round(combined_score, 6),
#             "weight_tg": weight_tg,
#             "weight_er": weight_er,
#         },
#         "error_values": {
#             "dtg": dtg,
#             "der": der,
#             "tol_tg": tol_tg,
#             "tol_er": tol_er,
#         },
#         "original_prompt": prompt,
#         "target_properties": {
#             "tg": target_tg,
#             "er": target_er,
#         },
#         "current_candidate": {
#             "monomer_1": monomer_1,
#             "monomer_2": monomer_2,
#         },
#         "predicted_properties": {
#             "tg": predicted_tg,
#             "er": predicted_er,
#         },
#         "diagnosis": {
#             "summary": summary,
#             "recommended_actions": recommended_actions,
#         },
#         "revision_instruction": {
#             "goal": revision_goal,
#         },
#         "optimization_mode": optimization_mode,
#     }

from typing import Any, Dict, List, Optional
from router.scoring import decide_optimization_mode


def build_property_revision_request(
    result: Dict[str, Any],
    default_tol_tg: float = 10.0,
    default_tol_er: float = 10.0,
    weight_tg: float = 0.5,
    weight_er: float = 0.5,
) -> Dict[str, Any]:
    def _to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def _safe_div(num: float, den: float) -> float:
        den = den if abs(den) > 1e-12 else 1e-12
        return num / den

    def _status(
        pred: Optional[float],
        target: Optional[float],
        tol: Optional[float],
    ) -> str:
        if pred is None or target is None or tol is None:
            return "unknown"
        if pred > target + tol:
            return "too_high"
        if pred < target - tol:
            return "too_low"
        return "matched"

    def _severity(norm_error: float) -> str:
        if norm_error <= 1.0:
            return "within_tolerance"
        if norm_error <= 1.5:
            return "moderate"
        if norm_error <= 2.5:
            return "high"
        return "very_high"

    property_details = result.get("property_details", {}) or {}

    prompt = result.get("prompt", "")
    monomer_1 = result.get("monomer_1", "")
    monomer_2 = result.get("monomer_2", "")

    target_tg = _to_float(
        result.get("target_tg"),
        _to_float(property_details.get("tg_target")),
    )
    target_er = _to_float(
        result.get("target_er"),
        _to_float(property_details.get("er_target")),
    )

    predicted_tg = _to_float(property_details.get("predicted_tg"))
    predicted_er = _to_float(property_details.get("predicted_er"))

    tol_tg = _to_float(property_details.get("tol_tg"), default_tol_tg)
    tol_er = _to_float(property_details.get("tol_er"), default_tol_er)

    dtg = _to_float(property_details.get("dtg"))
    if dtg is None and target_tg is not None and predicted_tg is not None:
        dtg = abs(predicted_tg - target_tg)

    der = _to_float(property_details.get("der"))
    if der is None and target_er is not None and predicted_er is not None:
        der = abs(predicted_er - target_er)

    tg_status = _status(predicted_tg, target_tg, tol_tg)
    er_status = _status(predicted_er, target_er, tol_er)

    normalized_dtg = _safe_div(
        dtg if dtg is not None else 0.0,
        tol_tg if tol_tg is not None else default_tol_tg,
    )
    normalized_der = _safe_div(
        der if der is not None else 0.0,
        tol_er if tol_er is not None else default_tol_er,
    )

    combined_score = (weight_tg * normalized_dtg) + (weight_er * normalized_der)
    decide_optimization_mode_result = decide_optimization_mode(result)
    print(f"Optimization mode: {decide_optimization_mode_result['mode']}")

    tg_needs_revision = dtg is not None and tol_tg is not None and dtg > tol_tg
    er_needs_revision = der is not None and tol_er is not None and der > tol_er

    needs_property_revision = bool(
        tg_needs_revision or er_needs_revision or result.get("is_agent_call_needed", False)
    )

    if tg_needs_revision and er_needs_revision:
        if normalized_dtg > normalized_der:
            priority_property = "tg"
        elif normalized_der > normalized_dtg:
            priority_property = "er"
        else:
            priority_property = "joint"
    elif tg_needs_revision:
        priority_property = "tg"
    elif er_needs_revision:
        priority_property = "er"
    else:
        priority_property = "none"

    recommended_actions: List[str] = []

    if tg_status == "too_high":
        recommended_actions.append("reduce predicted Tg")
    elif tg_status == "too_low":
        recommended_actions.append("increase predicted Tg")

    if er_status == "too_high":
        recommended_actions.append("reduce predicted Er")
    elif er_status == "too_low":
        recommended_actions.append("increase predicted Er")

    if not recommended_actions:
        recommended_actions.append("preserve current property alignment")

    summary_parts: List[str] = []

    if tg_status != "unknown":
        summary_parts.append(
            f"Predicted Tg is {predicted_tg} while target Tg is {target_tg} "
            f"(error={dtg}, tolerance={tol_tg}, status={tg_status})."
        )

    if er_status != "unknown":
        summary_parts.append(
            f"Predicted Er is {predicted_er} while target Er is {target_er} "
            f"(error={der}, tolerance={tol_er}, status={er_status})."
        )

    if priority_property == "tg":
        summary_parts.append("Revision should focus primarily on Tg correction.")
    elif priority_property == "er":
        summary_parts.append("Revision should focus primarily on Er correction.")
    elif priority_property == "joint":
        summary_parts.append("Revision should jointly optimize Tg and Er.")
    else:
        summary_parts.append("Property values are within tolerance; revision is optional.")

    summary = " ".join(summary_parts)

    revision_goal_parts: List[str] = []

    if tg_status == "too_high":
        revision_goal_parts.append("lower predicted Tg")
    elif tg_status == "too_low":
        revision_goal_parts.append("raise predicted Tg")

    if er_status == "too_high":
        revision_goal_parts.append("lower predicted Er")
    elif er_status == "too_low":
        revision_goal_parts.append("raise predicted Er")

    if revision_goal_parts:
        revision_goal = "Revise the monomer pair to " + " and ".join(revision_goal_parts) + "."
    else:
        revision_goal = "Preserve the current monomer pair because property targets are already satisfied."

    return {
        "needs_property_revision": needs_property_revision,
        "property_status": {
            "tg": tg_status,
            "er": er_status,
        },
        "severity": {
            "tg": _severity(normalized_dtg),
            "er": _severity(normalized_der),
        },
        "priority_property": priority_property,
        "scores": {
            "normalized_dtg": round(normalized_dtg, 6),
            "normalized_der": round(normalized_der, 6),
            "combined_score": round(combined_score, 6),
            "weight_tg": weight_tg,
            "weight_er": weight_er,
        },
        "error_values": {
            "dtg": dtg,
            "der": der,
            "tol_tg": tol_tg,
            "tol_er": tol_er,
        },
        "original_prompt": prompt,
        "target_properties": {
            "tg": target_tg,
            "er": target_er,
        },
        "current_candidate": {
            "monomer_1": monomer_1,
            "monomer_2": monomer_2,
        },
        "predicted_properties": {
            "tg": predicted_tg,
            "er": predicted_er,
        },
        "diagnosis": {
            "summary": summary,
            "recommended_actions": recommended_actions,
        },
        "revision_instruction": {
            "goal": revision_goal,
            "constraints": [
                "Return exactly two monomers.",
                "Keep the output in monomer form.",
                "Preserve important reactive functionality whenever possible.",
                "Make conservative edits for small gaps and stronger edits only when justified.",
            ],
        },
        "optimization_mode": decide_optimization_mode_result["mode"],
    }