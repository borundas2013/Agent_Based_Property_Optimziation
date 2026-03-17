from typing import Any, Dict

from .path_setup import ensure_generator_on_syspath

ensure_generator_on_syspath()

from Generator.property_constraints import check_tg_er_properties  # noqa: E402


def evaluate_revised_candidate(
    revised_candidate: Dict[str, Any],
    original_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evaluate a validated revised candidate with the property predictor.
    Assumes revised_monomer_1 and revised_monomer_2 are already validated.
    """
    revised_m1 = revised_candidate["revised_monomer_1"]
    revised_m2 = revised_candidate["revised_monomer_2"]

    target_tg = original_result["target_tg"]
    target_er = original_result["target_er"]

    original_prop = original_result.get("property_details", {})
    tol_tg = float(original_prop.get("tol_tg", 10.0))
    tol_er = float(original_prop.get("tol_er", 10.0))

    pred = check_tg_er_properties(
        revised_m1,
        revised_m2,
        target_tg,
        target_er,
        tol_tg,
        tol_er,
    )

    return {
        "prompt": original_result.get("prompt", ""),
        "target_tg": target_tg,
        "target_er": target_er,
        "monomer_1": revised_m1,
        "monomer_2": revised_m2,
        "property_details": {
            "tg_target": target_tg,
            "er_target": target_er,
            "predicted_tg": pred["predicted_tg"],
            "predicted_er": pred["predicted_er"],
            "dtg": pred["dtg"],
            "der": pred["der"],
            "tol_tg": pred.get("tol_tg", tol_tg),
            "tol_er": pred.get("tol_er", tol_er),
            "ratio_1": pred.get("ratio_1", 0.0),
            "ratio_2": pred.get("ratio_2", 0.0),
        },
        "revision_summary": revised_candidate.get("revision_summary", ""),
        "analysis": revised_candidate.get("analysis", {}),
        "validation_details": revised_candidate.get("validation_details", {}),
        "is_agent_call_needed": (
            pred["dtg"] > pred.get("tol_tg", tol_tg)
            or pred["der"] > pred.get("tol_er", tol_er)
        ),
    }

