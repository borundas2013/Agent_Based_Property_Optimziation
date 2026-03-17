from typing import Any, Dict, List, Optional


def extract_property_metrics(
    result: Dict[str, Any],
    default_tol_tg: float = 10.0,
    default_tol_er: float = 5.0,
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

    property_details = result.get("property_details", {}) or {}

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

    normalized_dtg = _safe_div(
        dtg if dtg is not None else 0.0,
        tol_tg if tol_tg is not None else default_tol_tg,
    )
    normalized_der = _safe_div(
        der if der is not None else 0.0,
        tol_er if tol_er is not None else default_tol_er,
    )

    if predicted_tg is None or target_tg is None:
        tg_direction = "unknown"
    elif predicted_tg < target_tg:
        tg_direction = "increase"
    elif predicted_tg > target_tg:
        tg_direction = "decrease"
    else:
        tg_direction = "keep"

    if predicted_er is None or target_er is None:
        er_direction = "unknown"
    elif predicted_er < target_er:
        er_direction = "increase"
    elif predicted_er > target_er:
        er_direction = "decrease"
    else:
        er_direction = "keep"

    return {
        "target_tg": target_tg,
        "target_er": target_er,
        "predicted_tg": predicted_tg,
        "predicted_er": predicted_er,
        "tol_tg": tol_tg,
        "tol_er": tol_er,
        "dtg": dtg,
        "der": der,
        "normalized_dtg": normalized_dtg,
        "normalized_der": normalized_der,
        "tg_direction": tg_direction,
        "er_direction": er_direction,
    }


def decide_optimization_mode(result: Dict[str, Any]) -> Dict[str, str]:
    metrics = extract_property_metrics(result)

    normalized_dtg = metrics["normalized_dtg"]
    normalized_der = metrics["normalized_der"]

    if normalized_dtg > 2.0 and normalized_dtg > normalized_der * 1.3:
        mode = "tg_first"
    elif normalized_der > 2.0 and normalized_der > normalized_dtg * 1.3:
        mode = "er_first"
    else:
        mode = "joint"

    return {
        "mode": mode,
        "tg_direction": metrics["tg_direction"],
        "er_direction": metrics["er_direction"],
    }


def build_property_revision_request(
    result: Dict[str, Any],
    default_tol_tg: float = 10.0,
    default_tol_er: float = 5.0,
    weight_tg: float = 0.5,
    weight_er: float = 0.5,
) -> Dict[str, Any]:
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

    metrics = extract_property_metrics(
        result,
        default_tol_tg=default_tol_tg,
        default_tol_er=default_tol_er,
    )

    mode_info = decide_optimization_mode(result)

    prompt = result.get("prompt", "")
    monomer_1 = result.get("monomer_1", "")
    monomer_2 = result.get("monomer_2", "")

    target_tg = metrics["target_tg"]
    target_er = metrics["target_er"]
    predicted_tg = metrics["predicted_tg"]
    predicted_er = metrics["predicted_er"]
    tol_tg = metrics["tol_tg"]
    tol_er = metrics["tol_er"]
    dtg = metrics["dtg"]
    der = metrics["der"]
    normalized_dtg = metrics["normalized_dtg"]
    normalized_der = metrics["normalized_der"]
    tg_direction = metrics["tg_direction"]
    er_direction = metrics["er_direction"]

    combined_score = (weight_tg * normalized_dtg) + (weight_er * normalized_der)

    tg_status = _status(predicted_tg, target_tg, tol_tg)
    er_status = _status(predicted_er, target_er, tol_er)

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

    if tg_direction == "increase":
        recommended_actions.append("increase predicted Tg")
    elif tg_direction == "decrease":
        recommended_actions.append("decrease predicted Tg")

    if er_direction == "increase":
        recommended_actions.append("increase predicted Er")
    elif er_direction == "decrease":
        recommended_actions.append("decrease predicted Er")

    if not recommended_actions:
        recommended_actions.append("preserve current property alignment")

    summary_parts: List[str] = []

    if tg_status != "unknown":
        summary_parts.append(
            f"Predicted Tg is {predicted_tg} while target Tg is {target_tg} "
            f"(error={dtg}, tolerance={tol_tg}, status={tg_status}, direction={tg_direction})."
        )

    if er_status != "unknown":
        summary_parts.append(
            f"Predicted Er is {predicted_er} while target Er is {target_er} "
            f"(error={der}, tolerance={tol_er}, status={er_status}, direction={er_direction})."
        )

    if priority_property == "tg":
        summary_parts.append("Revision should focus primarily on Tg correction.")
    elif priority_property == "er":
        summary_parts.append("Revision should focus primarily on Er correction.")
    elif priority_property == "joint":
        summary_parts.append("Revision should jointly optimize Tg and Er.")
    else:
        summary_parts.append("Property values are within tolerance; revision is optional.")

    summary_parts.append(f"Recommended optimization mode is {mode_info['mode']}.")

    summary = " ".join(summary_parts)

    revision_goal_parts: List[str] = []

    if tg_direction == "increase":
        revision_goal_parts.append("raise predicted Tg")
    elif tg_direction == "decrease":
        revision_goal_parts.append("lower predicted Tg")

    if er_direction == "increase":
        revision_goal_parts.append("raise predicted Er")
    elif er_direction == "decrease":
        revision_goal_parts.append("lower predicted Er")

    if revision_goal_parts and needs_property_revision:
        revision_goal = "Revise the monomer pair to " + " and ".join(revision_goal_parts) + "."
    else:
        revision_goal = "Preserve the current monomer pair because property targets are already satisfied."

    return {
        "needs_property_revision": needs_property_revision,
        "optimization_mode": mode_info["mode"],
        "property_direction": {
            "tg": tg_direction,
            "er": er_direction,
        },
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
                "Use conservative edits for small gaps and stronger but justified edits for large gaps.",
                "Follow the optimization mode and property directions strictly.",
            ],
        },
    }