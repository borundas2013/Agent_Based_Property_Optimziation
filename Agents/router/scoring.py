from typing import Any, Dict



def compute_combined_score(result: Dict[str, Any]) -> float:
    """
    Lower is better.
    Score = normalized Tg error + normalized Er error
    """
    prop = result.get("property_details", {})

    dtg = float(prop.get("dtg", 1e9))
    der = float(prop.get("der", 1e9))
    tol_tg = float(prop.get("tol_tg", 10.0))
    tol_er = float(prop.get("tol_er", 10.0))

    normalized_dtg = dtg / tol_tg if tol_tg > 0 else 1e9
    normalized_der = der / tol_er if tol_er > 0 else 1e9

    return normalized_dtg + normalized_der

def decide_optimization_mode(result: Dict[str, Any]) -> str:
    """
    Decide whether to optimize Tg first, Er first, or jointly.
    """

    prop = result.get("property_details", {})

    dtg = float(prop.get("dtg", 1e9))
    der = float(prop.get("der", 1e9))
    tol_tg = float(prop.get("tol_tg", 10.0))
    tol_er = float(prop.get("tol_er", 10.0))

    normalized_dtg = dtg / tol_tg if tol_tg > 0 else 1e9
    normalized_der = der / tol_er if tol_er > 0 else 1e9

    if normalized_dtg > 2.0 and normalized_dtg > normalized_der * 1.3:
        return "tg_first"

    elif normalized_der > 2.0 and normalized_der > normalized_dtg * 1.3:
        return "er_first"

    return "joint"

def decide_optimization_mode(result: Dict[str, Any]) -> Dict[str, str]:
    """
    Decide which property to optimize and in which direction.
    """

    prop = result.get("property_details", {})

    predicted_tg = float(prop.get("predicted_tg", 0.0))
    predicted_er = float(prop.get("predicted_er", 0.0))
    target_tg = float(prop.get("tg_target", 0.0))
    target_er = float(prop.get("er_target", 0.0))

    dtg = abs(predicted_tg - target_tg)
    der = abs(predicted_er - target_er)

    tol_tg = float(prop.get("tol_tg", 10.0))
    tol_er = float(prop.get("tol_er", 10.0))

    normalized_dtg = dtg / tol_tg if tol_tg > 0 else 1e9
    normalized_der = der / tol_er if tol_er > 0 else 1e9

    # ---- direction ----
    tg_direction = "increase" if predicted_tg < target_tg else "decrease"
    er_direction = "increase" if predicted_er < target_er else "decrease"

    # ---- mode decision ----
    if normalized_dtg > 2.0 and normalized_dtg > normalized_der * 1.3:
        mode = "tg_first"

    elif normalized_der > 2.0 and normalized_der > normalized_dtg * 1.3:
        mode = "er_first"

    else:
        mode = "joint"

    return {
        "mode": mode,
        "tg_direction": tg_direction,
        "er_direction": er_direction,
    }

def compute_error_metrics(result: Dict[str, Any]) -> Dict[str, float]:
    prop = result.get("property_details", {})

    dtg = float(prop.get("dtg", 1e9))
    der = float(prop.get("der", 1e9))
    tol_tg = float(prop.get("tol_tg", 10.0))
    tol_er = float(prop.get("tol_er", 10.0))

    normalized_dtg = dtg / tol_tg if tol_tg > 0 else 1e9
    normalized_der = der / tol_er if tol_er > 0 else 1e9

    return {
        "normalized_dtg": normalized_dtg,
        "normalized_der": normalized_der,
        "combined_score": normalized_dtg + normalized_der,
    }

def is_within_tolerance(result: Dict[str, Any]) -> bool:
    prop = result.get("property_details", {})
    dtg = float(prop.get("dtg", 1e9))
    der = float(prop.get("der", 1e9))
    tol_tg = float(prop.get("tol_tg", 10.0))
    tol_er = float(prop.get("tol_er", 10.0))
    return dtg <= tol_tg and der <= tol_er

