from typing import Any, Dict

from .property_evaluation import evaluate_revised_candidate

from LLM_Reviser.repair_mechanism import (  # noqa: E402
    safe_parse_llm_output,
    validate_revised_candidate,
)
from router.request_builder import build_property_revision_request

def parse_llm_json(raw_text: str) -> Dict[str, Any]:
    """
    Wrapper around safe_parse_llm_output() so this package has one consistent contract.
    Expected return:
    {
        "ok": bool,
        "data": dict | None,
        "error": str | None
    }
    """
    parsed = safe_parse_llm_output(raw_text)

    if not isinstance(parsed, dict):
        return {
            "ok": False,
            "data": None,
            "error": "safe_parse_llm_output returned invalid format",
        }

    return {
        "ok": bool(parsed.get("ok", False)),
        "data": parsed.get("data"),
        "error": parsed.get("error", "Unknown parse error"),
    }




def process_llm_revision(
    raw_llm_output: str,
    original_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Pipeline:
    1. Parse initial LLM output
    2. Validate candidate
    3. If valid -> canonicalize + evaluate properties
    """

    initial_raw_response = raw_llm_output

    def _reject(
        status: str,
        reason: str,
        validation: Dict[str, Any] = None,
        parsed_candidate: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        return {
            "status": status,
            "accepted": False,
            "reason": reason,
            "evaluated_result": None,
            "validation": validation,
            "parsed_candidate": parsed_candidate,
            "raw_response": initial_raw_response,
        }

    
    if "optimization_mode" not in original_result or "priority_property" not in original_result:
        request_meta = build_property_revision_request(original_result)
        original_result = {
            **original_result,
            "optimization_mode": request_meta.get("optimization_mode", "joint"),
            "priority_property": request_meta.get("priority_property", "none"),
        }
    # -------------------------------------------------
    # Step 1: Parse initial output
    # -------------------------------------------------
    parse_result = parse_llm_json(raw_llm_output)

    if not parse_result["ok"]:
        return _reject(
            status="parse_failed",
            reason=parse_result["error"],
            validation=None,
            parsed_candidate=None,
        )
    candidate = parse_result["data"]

    # Defensive check
    if not isinstance(candidate, dict):
        return _reject(
            status="candidate_not_dict",
            reason="Parsed candidate is not a dictionary",
            validation=None,
            parsed_candidate=candidate,
        )

    # -------------------------------------------------
    # Step 2: Validate parsed candidate
    # -------------------------------------------------
    validation = validate_revised_candidate(
        revised_m1=candidate.get("revised_monomer_1", ""),
        revised_m2=candidate.get("revised_monomer_2", ""),
    )

    # -------------------------------------------------
    # Step 3: Reject on validation failure
    # -------------------------------------------------
    if not validation.get("valid", False):
        return _reject(
            status="validation_failed",
            reason="; ".join(validation.get("errors", ["Unknown validation failure"])),
            validation=validation,
            parsed_candidate=candidate,
        )

    # -------------------------------------------------
    # Step 4: Canonicalize accepted candidate
    # -------------------------------------------------
    candidate["revised_monomer_1"] = validation["canonical"]["monomer_1"]
    candidate["revised_monomer_2"] = validation["canonical"]["monomer_2"]

    # -------------------------------------------------
    # Step 5: Evaluate accepted candidate
    # -------------------------------------------------
    evaluated_result = evaluate_revised_candidate(candidate, original_result)
    evaluated_result["validation_details"] = validation
    if "focus_property" in original_result:
        evaluated_result["focus_property"] = original_result["focus_property"]

    return {
        "status": "success",
        "accepted": True,
        "reason": "validated_and_evaluated",
        "evaluated_result": evaluated_result,
        "parsed_candidate": candidate,
        "validation": validation,
        "raw_response": initial_raw_response,
        "repair_response": None,
    }


