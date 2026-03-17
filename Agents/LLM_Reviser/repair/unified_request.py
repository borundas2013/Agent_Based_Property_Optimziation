# from typing import Any, Dict


# REPAIR_SYSTEM_PROMPT = """You are an expert polymer refinement agent for two-monomer thermoset shape memory polymer (TSMP) design.

# Your task is to analyze a candidate monomer pair, diagnose why it fails or underperforms, and produce a corrected revised monomer pair that is more likely to move toward the target Tg and Er while preserving chemical plausibility and reactive suitability.

# You must handle both:
# 1. normal refinement requests, and
# 2. repair requests when the previous revised monomers were invalid, malformed, chemically implausible, or lost important reactive functionality.

# Follow these rules strictly:

# 1. Analyze the property gap:
#    - Determine whether Tg should increase, decrease, or remain stable.
#    - Determine whether Er should increase, decrease, or remain stable.

# 2. Analyze the error reason:
#    - Inspect validation errors such as invalid SMILES, missing keys, loss of reactive groups, over-editing, or poor structural plausibility.
#    - If current revised monomers are invalid, repair them.
#    - If current revised monomers are missing or unusable, start from the original monomers.

# 3. Preserve chemistry:
#    - Keep the monomers chemically plausible.
#    - Preserve important reactive groups and polymerizable functionality from the original monomers whenever possible.
#    - Do not remove essential reactive handles unless replaced by a chemically compatible alternative.

# 4. Minimize unnecessary edits:
#    - Prefer minimal but meaningful changes.
#    - Do not redesign both monomers aggressively unless absolutely necessary.
#    - If only one monomer needs change, keep the other unchanged.

# 5. Maintain the intended optimization direction:
#    - Increase rigidity/aromaticity/polar rigidity when Tg must increase.
#    - Increase flexibility or reduce rigidity when Tg must decrease.
#    - Balance flexibility and crosslink-supporting chemistry appropriately for Er adjustment.
#    - Avoid improving one property by severely damaging the other.

# 6. If the safest action is to keep one or both original monomers unchanged, do so.

# 7. Return output as valid JSON only.
#    Do not include markdown fences, explanations outside JSON, or extra commentary.

# Return exactly this schema:
# {
#   "analysis": {
#     "tg_direction": "increase|decrease|keep",
#     "er_direction": "increase|decrease|keep",
#     "error_diagnosis": ["..."],
#     "edit_strategy": ["..."]
#   },
#   "revised_monomer_1": "...",
#   "revised_monomer_2": "...",
#   "revision_summary": "..."
# }
# """


# def build_unified_revision_request(
#     original_result: Dict[str, Any],
#     candidate_result: Dict[str, Any] = None,
#     validation_errors: list | None = None,
#     parse_error: str | None = None,
# ) -> Dict[str, Any]:
#     property_details = original_result.get("property_details", {})

#     original_m1 = original_result["monomer_1"]
#     original_m2 = original_result["monomer_2"]

#     candidate_m1 = ""
#     candidate_m2 = ""
#     revision_summary = ""

#     if candidate_result is not None:
#         candidate_m1 = candidate_result.get("revised_monomer_1", "")
#         candidate_m2 = candidate_result.get("revised_monomer_2", "")
#         revision_summary = candidate_result.get("revision_summary", "")

#     target_tg = original_result["target_tg"]
#     target_er = original_result["target_er"]
#     predicted_tg = property_details.get("predicted_tg")
#     predicted_er = property_details.get("predicted_er")

#     delta_tg = None if predicted_tg is None else target_tg - predicted_tg
#     delta_er = None if predicted_er is None else target_er - predicted_er

#     return {
#         "original_monomer_1": original_m1,
#         "original_monomer_2": original_m2,
#         "candidate_monomer_1": candidate_m1,
#         "candidate_monomer_2": candidate_m2,
#         "target_tg": target_tg,
#         "target_er": target_er,
#         "predicted_tg": predicted_tg,
#         "predicted_er": predicted_er,
#         "delta_tg": delta_tg,
#         "delta_er": delta_er,
#         "validation_errors": validation_errors or [],
#         "parse_error": parse_error or "",
#         "previous_revision_summary": revision_summary,
#     }


# def make_unified_revision_messages(revision_request: Dict[str, Any]):
#     system_message = {
#         "role": "system",
#         "content": REPAIR_SYSTEM_PROMPT,
#     }

#     user_message = {
#         "role": "user",
#         "content": f"""
# Refinement context:

# Original monomer 1: {revision_request['original_monomer_1']}
# Original monomer 2: {revision_request['original_monomer_2']}

# Current candidate monomer 1: {revision_request['candidate_monomer_1']}
# Current candidate monomer 2: {revision_request['candidate_monomer_2']}

# Target Tg: {revision_request['target_tg']}
# Target Er: {revision_request['target_er']}

# Predicted Tg: {revision_request['predicted_tg']}
# Predicted Er: {revision_request['predicted_er']}

# Tg gap: {revision_request['delta_tg']}
# Er gap: {revision_request['delta_er']}

# Parse error:
# {revision_request['parse_error']}

# Validation errors:
# {revision_request['validation_errors']}





# Please analyze the error state, determine how Tg and Er should change, and return corrected revised monomers.
# Return JSON only.
# """,
#     }

#     return [system_message, user_message]

from typing import Any, Dict


REPAIR_SYSTEM_PROMPT = """You are an expert polymer refinement and repair agent for two-monomer thermoset shape memory polymer (TSMP) design.

Your task is to repair or revise a candidate monomer pair so that it is:
1. valid and parseable,
2. chemically plausible,
3. reactive-functionality-aware,
4. better aligned with the requested target Tg and Er.

You must handle both:
- formatting/JSON repair, and
- chemistry-aware candidate repair or refinement.

Follow these rules strictly:

1. Respect optimization intent:
   - Use the provided optimization mode, priority property, and property directions.
   - If Tg should increase, prefer more rigidity, aromaticity, cyclic constraint, or reduced excessive flexibility.
   - If Tg should decrease, prefer more flexibility or reduced excessive rigidity.
   - If Er should increase, prefer preserving or improving reactive/crosslink-supporting functionality and mechanically supportive structure.
   - If Er should decrease, prefer reducing excessive stiffness or overly strong crosslink-driving features while preserving valid reactive functionality.

2. Analyze the error reason:
   - If the issue is only malformed JSON or formatting, preserve the candidate chemistry as much as possible and fix the output format.
   - If the candidate monomers are invalid, chemically implausible, or lost important reactive functionality, repair them.
   - If the current candidate is unusable, start conservatively from the original monomers.

3. Preserve chemistry:
   - Keep monomers chemically plausible.
   - Preserve important reactive/polymerizable functionality whenever possible.
   - Do not remove essential reactive handles unless replaced by a chemically compatible alternative.

4. Control edit size:
   - Prefer minimal but meaningful changes when the gap is small.
   - Stronger redesign is allowed only when the gap is large or the candidate is badly invalid.
   - Do not redesign both monomers aggressively unless necessary.

5. Protect already-good properties:
   - Avoid improving one property by severely damaging the other.
   - Preserve properties already within tolerance whenever reasonably possible.

6. If the safest action is to keep one or both original monomers unchanged, do so.

7. Return output as valid JSON only.
   Do not include markdown fences, explanations outside JSON, or extra commentary.

Return exactly this schema:
{
  "revised_monomer_1": "...",
  "revised_monomer_2": "...",
  "revision_summary": "..."
}
"""


def build_unified_revision_request(
    original_result: Dict[str, Any],
    candidate_result: Dict[str, Any] = None,
    validation_errors: list | None = None,
    parse_error: str | None = None,
) -> Dict[str, Any]:
    property_details = original_result.get("property_details", {}) or {}

    original_m1 = original_result.get("monomer_1", "")
    original_m2 = original_result.get("monomer_2", "")

    candidate_m1 = ""
    candidate_m2 = ""
    revision_summary = ""

    if candidate_result is not None:
        candidate_m1 = candidate_result.get("revised_monomer_1", "")
        candidate_m2 = candidate_result.get("revised_monomer_2", "")
        revision_summary = candidate_result.get("revision_summary", "")

    target_tg = original_result.get("target_tg", property_details.get("tg_target"))
    target_er = original_result.get("target_er", property_details.get("er_target"))
    predicted_tg = property_details.get("predicted_tg")
    predicted_er = property_details.get("predicted_er")

    delta_tg = None if predicted_tg is None or target_tg is None else target_tg - predicted_tg
    delta_er = None if predicted_er is None or target_er is None else target_er - predicted_er

    optimization_mode = original_result.get("optimization_mode", "joint")
    priority_property = original_result.get("priority_property", "none")

    tg_direction = "unknown"
    if delta_tg is not None:
        if delta_tg > 0:
            tg_direction = "increase"
        elif delta_tg < 0:
            tg_direction = "decrease"
        else:
            tg_direction = "keep"

    er_direction = "unknown"
    if delta_er is not None:
        if delta_er > 0:
            er_direction = "increase"
        elif delta_er < 0:
            er_direction = "decrease"
        else:
            er_direction = "keep"

    return {
        "original_monomer_1": original_m1,
        "original_monomer_2": original_m2,
        "candidate_monomer_1": candidate_m1,
        "candidate_monomer_2": candidate_m2,
        "target_tg": target_tg,
        "target_er": target_er,
        "predicted_tg": predicted_tg,
        "predicted_er": predicted_er,
        "delta_tg": delta_tg,
        "delta_er": delta_er,
        "optimization_mode": optimization_mode,
        "priority_property": priority_property,
        "tg_direction": tg_direction,
        "er_direction": er_direction,
        "validation_errors": validation_errors or [],
        "parse_error": parse_error or "",
        "previous_revision_summary": revision_summary,
    }


def make_unified_revision_messages(revision_request: Dict[str, Any]):
    system_message = {
        "role": "system",
        "content": REPAIR_SYSTEM_PROMPT,
    }

    user_message = {
        "role": "user",
        "content": f"""
Refinement context:

Original monomer 1: {revision_request['original_monomer_1']}
Original monomer 2: {revision_request['original_monomer_2']}

Current candidate monomer 1: {revision_request['candidate_monomer_1']}
Current candidate monomer 2: {revision_request['candidate_monomer_2']}

Target Tg: {revision_request['target_tg']}
Target Er: {revision_request['target_er']}

Predicted Tg: {revision_request['predicted_tg']}
Predicted Er: {revision_request['predicted_er']}

Tg gap: {revision_request['delta_tg']}
Er gap: {revision_request['delta_er']}

Optimization mode: {revision_request['optimization_mode']}
Priority property: {revision_request['priority_property']}
Tg direction: {revision_request['tg_direction']}
Er direction: {revision_request['er_direction']}

Parse error:
{revision_request['parse_error']}

Validation errors:
{revision_request['validation_errors']}

Previous revision summary:
{revision_request['previous_revision_summary']}

Instructions:
- If the issue is mainly JSON/formatting, preserve the current candidate chemistry as much as possible and fix the JSON.
- If the candidate monomers are invalid or chemically unsuitable, repair them conservatively.
- Preserve important reactive/polymerizable functionality whenever possible.
- Follow the optimization mode and property directions.
- Return JSON only.

Return exactly this schema:
{{
  "revised_monomer_1": "...",
  "revised_monomer_2": "...",
  "revision_summary": "..."
}}
""",
    }

    return [system_message, user_message]
