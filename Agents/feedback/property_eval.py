from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from Predictor_Agent.property_check.property_checker import PropertyChecker


def check_tg_er_properties(
    monomer_1: str,
    monomer_2: str,
    target_tg: float,
    target_er: float,
    tol_tg: Optional[float] = None,
    tol_er: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    return check_property(
        monomer_1=monomer_1,
        monomer_2=monomer_2,
        target_tg=target_tg,
        target_er=target_er,
        tol_tg=tol_tg,
        tol_er=tol_er,
    )


def check_property(
    monomer_1: str,
    monomer_2: str,
    target_tg: float,
    target_er: float,
    tol_tg: Optional[float] = None,
    tol_er: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    property_checker = PropertyChecker()

    tol_tg = float(tol_tg) if tol_tg is not None else float(property_checker.tol_tg)
    tol_er = float(tol_er) if tol_er is not None else float(property_checker.tol_er)

    best_result: Optional[Dict[str, Any]] = None
    best_score: Optional[Tuple[float, float, float]] = None

    for i in range(1, 10):
        ratio_1 = round(i / 10.0, 1)
        ratio_2 = round(1.0 - ratio_1, 1)

        try:
            result = property_checker(
                monomer_1=monomer_1,
                monomer_2=monomer_2,
                tg_target=target_tg,
                er_target=target_er,
                ratio_1=ratio_1,
                ratio_2=ratio_2,
            )
        except Exception:
            continue

        if result is None:
            continue

        dtg = float(result.get("dtg", 1e9))
        der = float(result.get("der", 1e9))
        pred_tg = result.get("predicted_tg", result.get("tg_pred", None))
        pred_er = result.get("predicted_er", result.get("er_pred", None))

        over_tg = max(dtg - tol_tg, 0.0)
        over_er = max(der - tol_er, 0.0)

        score = (over_tg + over_er, dtg + der, abs(dtg - der))

        if best_score is None or score < best_score:
            best_score = score
            best_result = {
                **result,
                "predicted_tg": pred_tg,
                "predicted_er": pred_er,
                "ratio_1": ratio_1,
                "ratio_2": ratio_2,
                "tol_tg": tol_tg,
                "tol_er": tol_er,
                "within_tg_tolerance": dtg <= tol_tg,
                "within_er_tolerance": der <= tol_er,
                "within_property_tolerance": (dtg <= tol_tg and der <= tol_er),
            }

    return best_result
