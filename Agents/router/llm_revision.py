from typing import Any, Dict

from .property_evaluation import evaluate_revised_candidate

from LLM_Reviser.property_refinement_element import (  # noqa: E402
    call_repaird_llm_reviser,
)
from LLM_Reviser.repair_mechanism import (  # noqa: E402
    build_unified_revision_request,
    make_unified_revision_messages,
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


# def process_llm_revision(
#     raw_llm_output: str,
#     original_result: Dict[str, Any],
# ) -> Dict[str, Any]:
#     """
#     Pipeline:
#     1. Parse initial LLM output
#     2. If parse fails -> retry once with repair agent
#     3. Validate candidate
#     4. If validation fails -> retry once with repair agent
#     5. If valid -> canonicalize + evaluate properties
#     """
#     initial_raw_response = raw_llm_output

#     # -------------------------------------------------
#     # Step 1: Parse initial output
#     # -------------------------------------------------
#     parse_result = parse_llm_json(raw_llm_output)

#     if parse_result["ok"]:
#         candidate = parse_result["data"]
#     else:
#         candidate = None

#     # -------------------------------------------------
#     # Step 2: Retry on parse failure
#     # -------------------------------------------------
#     if not parse_result["ok"]:
#         repair_request = build_unified_revision_request(
#             original_result=original_result,
#             candidate_result=None,
#             validation_errors=[],
#             parse_error=parse_result["error"],
#         )
#         messages = make_unified_revision_messages(repair_request)

#         repaired_raw = call_repaird_llm_reviser(messages)

#         repaired_parse = parse_llm_json(repaired_raw)

#         if not repaired_parse["ok"]:
#             return {
#                 "status": "parse_failed_after_retry",
#                 "accepted": False,
#                 "reason": repaired_parse["error"],
#                 "evaluated_result": None,
#                 "validation": None,
#                 "parsed_candidate": None,
#                 "raw_response": initial_raw_response,
#                 "repair_response": repaired_raw,
#             }

#         candidate = repaired_parse["data"]
#     else:
#         repaired_raw = None

#     # Defensive check
#     if not isinstance(candidate, dict):
#         return {
#             "status": "candidate_not_dict",
#             "accepted": False,
#             "reason": "Parsed candidate is not a dictionary",
#             "evaluated_result": None,
#             "validation": None,
#             "parsed_candidate": candidate,
#             "raw_response": initial_raw_response,
#             "repair_response": repaired_raw,
#         }

#     # -------------------------------------------------
#     # Step 3: Validate parsed candidate
#     # -------------------------------------------------
#     validation = validate_revised_candidate(
#         revised_m1=candidate.get("revised_monomer_1", ""),
#         revised_m2=candidate.get("revised_monomer_2", ""),
#     )

#     # -------------------------------------------------
#     # Step 4: Retry on validation failure
#     # -------------------------------------------------
#     if not validation.get("valid", False):
#         repair_request = build_unified_revision_request(
#             original_result=original_result,
#             candidate_result=candidate,
#             validation_errors=validation.get("errors", []),
#             parse_error="",
#         )

#         messages = make_unified_revision_messages(repair_request)
#         repaired_raw = call_repaird_llm_reviser(messages)
#         repaired_parse = parse_llm_json(repaired_raw)

#         if not repaired_parse["ok"]:
#             return {
#                 "status": "validation_repair_parse_failed",
#                 "accepted": False,
#                 "reason": repaired_parse["error"],
#                 "evaluated_result": None,
#                 "validation": validation,
#                 "parsed_candidate": candidate,
#                 "raw_response": initial_raw_response,
#                 "repair_response": repaired_raw,
#             }

#         repaired_candidate = repaired_parse["data"]

#         if not isinstance(repaired_candidate, dict):
#             return {
#                 "status": "validation_repair_candidate_not_dict",
#                 "accepted": False,
#                 "reason": "Repaired candidate is not a dictionary",
#                 "evaluated_result": None,
#                 "validation": validation,
#                 "parsed_candidate": repaired_candidate,
#                 "raw_response": initial_raw_response,
#                 "repair_response": repaired_raw,
#             }

#         repaired_validation = validate_revised_candidate(
#             revised_m1=repaired_candidate.get("revised_monomer_1", ""),
#             revised_m2=repaired_candidate.get("revised_monomer_2", ""),
#         )

#         if not repaired_validation.get("valid", False):
#             return {
#                 "status": "validation_failed_after_retry",
#                 "accepted": False,
#                 "reason": "; ".join(
#                     repaired_validation.get("errors", ["Unknown validation failure"])
#                 ),
#                 "evaluated_result": None,
#                 "validation": repaired_validation,
#                 "parsed_candidate": repaired_candidate,
#                 "raw_response": initial_raw_response,
#                 "repair_response": repaired_raw,
#             }

#         candidate = repaired_candidate
#         validation = repaired_validation

#     # -------------------------------------------------
#     # Step 5: Canonicalize accepted candidate
#     # -------------------------------------------------
#     candidate["revised_monomer_1"] = validation["canonical"]["monomer_1"]
#     candidate["revised_monomer_2"] = validation["canonical"]["monomer_2"]

#     # -------------------------------------------------
#     # Step 6: Evaluate accepted candidate
#     # -------------------------------------------------
#     evaluated_result = evaluate_revised_candidate(candidate, original_result)
#     evaluated_result["validation_details"] = validation

#     return {
#         "status": "success",
#         "accepted": True,
#         "reason": "validated_and_evaluated",
#         "evaluated_result": evaluated_result,
#         "parsed_candidate": candidate,
#         "validation": validation,
#         "raw_response": initial_raw_response,
#         "repair_response": repaired_raw,
#     }


def process_llm_revision(
    raw_llm_output: str,
    original_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Pipeline:
    1. Parse initial LLM output
    2. If parse fails -> retry once with repair agent
    3. Validate candidate
    4. If validation fails -> retry once with repair agent
    5. If valid -> canonicalize + evaluate properties
    """

    initial_raw_response = raw_llm_output
    repair_response = None

    def _reject(
        status: str,
        reason: str,
        validation: Dict[str, Any] = None,
        parsed_candidate: Dict[str, Any] = None,
        repair_response_local: str = None,
    ) -> Dict[str, Any]:
        return {
            "status": status,
            "accepted": False,
            "reason": reason,
            "evaluated_result": None,
            "validation": validation,
            "parsed_candidate": parsed_candidate,
            "raw_response": initial_raw_response,
            "repair_response": repair_response_local,
        }

    def _repair_candidate(
        candidate_result: Dict[str, Any] = None,
        validation_errors: list | None = None,
        parse_error: str | None = None,
    ) -> Dict[str, Any]:
        repair_request = build_unified_revision_request(
            original_result=original_result,
            candidate_result=candidate_result,
            validation_errors=validation_errors or [],
            parse_error=parse_error or "",
        )
        messages = make_unified_revision_messages(repair_request)
        repaired_raw_local = call_repaird_llm_reviser(messages)
        repaired_parse_local = parse_llm_json(repaired_raw_local)

        return {
            "raw": repaired_raw_local,
            "parse": repaired_parse_local,
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

    if parse_result["ok"]:
        candidate = parse_result["data"]
    else:
        candidate = None

    # -------------------------------------------------
    # Step 2: Retry on parse failure
    # -------------------------------------------------
    if not parse_result["ok"]:
        repaired = _repair_candidate(
            candidate_result=None,
            validation_errors=[],
            parse_error=parse_result["error"],
        )
        repair_response = repaired["raw"]
        repaired_parse = repaired["parse"]

        if not repaired_parse["ok"]:
            return _reject(
                status="parse_failed_after_retry",
                reason=repaired_parse["error"],
                validation=None,
                parsed_candidate=None,
                repair_response_local=repair_response,
            )

        candidate = repaired_parse["data"]

    # Defensive check
    if not isinstance(candidate, dict):
        return _reject(
            status="candidate_not_dict",
            reason="Parsed candidate is not a dictionary",
            validation=None,
            parsed_candidate=candidate,
            repair_response_local=repair_response,
        )

    # -------------------------------------------------
    # Step 3: Validate parsed candidate
    # -------------------------------------------------
    validation = validate_revised_candidate(
        revised_m1=candidate.get("revised_monomer_1", ""),
        revised_m2=candidate.get("revised_monomer_2", ""),
    )

    # -------------------------------------------------
    # Step 4: Retry on validation failure
    # -------------------------------------------------
    if not validation.get("valid", False):
        repaired = _repair_candidate(
            candidate_result=candidate,
            validation_errors=validation.get("errors", []),
            parse_error="",
        )
        repair_response = repaired["raw"]
        repaired_parse = repaired["parse"]

        if not repaired_parse["ok"]:
            return _reject(
                status="validation_repair_parse_failed",
                reason=repaired_parse["error"],
                validation=validation,
                parsed_candidate=candidate,
                repair_response_local=repair_response,
            )

        repaired_candidate = repaired_parse["data"]

        if not isinstance(repaired_candidate, dict):
            return _reject(
                status="validation_repair_candidate_not_dict",
                reason="Repaired candidate is not a dictionary",
                validation=validation,
                parsed_candidate=repaired_candidate,
                repair_response_local=repair_response,
            )

        repaired_validation = validate_revised_candidate(
            revised_m1=repaired_candidate.get("revised_monomer_1", ""),
            revised_m2=repaired_candidate.get("revised_monomer_2", ""),
        )

        if not repaired_validation.get("valid", False):
            return _reject(
                status="validation_failed_after_retry",
                reason="; ".join(
                    repaired_validation.get("errors", ["Unknown validation failure"])
                ),
                validation=repaired_validation,
                parsed_candidate=repaired_candidate,
                repair_response_local=repair_response,
            )

        candidate = repaired_candidate
        validation = repaired_validation

    # -------------------------------------------------
    # Step 5: Canonicalize accepted candidate
    # -------------------------------------------------
    candidate["revised_monomer_1"] = validation["canonical"]["monomer_1"]
    candidate["revised_monomer_2"] = validation["canonical"]["monomer_2"]

    # -------------------------------------------------
    # Step 6: Evaluate accepted candidate
    # -------------------------------------------------
    evaluated_result = evaluate_revised_candidate(candidate, original_result)
    evaluated_result["validation_details"] = validation

    return {
        "status": "success",
        "accepted": True,
        "reason": "validated_and_evaluated",
        "evaluated_result": evaluated_result,
        "parsed_candidate": candidate,
        "validation": validation,
        "raw_response": initial_raw_response,
        "repair_response": repair_response,
    }