import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .path_setup import ensure_generator_on_syspath
from .scoring import compute_combined_score, is_within_tolerance
from .llm_revision import process_llm_revision
from .request_builder import build_property_revision_request

ensure_generator_on_syspath()

from Generator.property_constraints import read_json_from_file  # noqa: E402
from LLM_Reviser.property_refinement_element import call_llm_reviser  # noqa: E402


def evaluate(
    input_json_path: str = str(Path("Evaluations") / "prompts" / "property_prompt_sample_100.json"),
    max_iterations: int = 3,
) -> Optional[Dict[str, Any]]:
    result = read_json_from_file(input_json_path)

    if result is None:
        print("No valid result returned from read_json_from_file.")
        return None

    initial_result = result
    best_result = result
    best_score = compute_combined_score(best_result)

    candidates: List[Dict[str, Any]] = [result]

    if not result.get("is_agent_call_needed", False):
        print("Agent call not needed")
        print("--------------------------------")
        print(best_result)

    print("Original candidate:")
    print(f"  Monomer 1: {best_result.get('monomer_1')}")
    print(f"  Monomer 2: {best_result.get('monomer_2')}")
    print(f"  Property details: {best_result['property_details']}")
    print(f"  Score: {best_score:.4f}")
    print("Agent call needed")
    print("--------------------------------")

    for step in range(max_iterations):
        print(f"\n--- Revision iteration {step + 1} ---")

        request = build_property_revision_request(best_result)
        raw_response = call_llm_reviser(request)

        print("LLM reviser raw response:")
        print(raw_response)

        processed = process_llm_revision(raw_response, best_result)

        if not processed["accepted"]:
            print("Revision rejected:")
            print(processed["reason"])

            rejected_record = {
                "status": processed.get("status"),
                "accepted": False,
                "reason": processed.get("reason"),
                "raw_response": processed.get("raw_response"),
                "repair_response": processed.get("repair_response"),
                "parsed_candidate": processed.get("parsed_candidate"),
                "validation": processed.get("validation"),
            }
            candidates.append(rejected_record)
            continue

        revised_result = processed["evaluated_result"]
        revised_score = compute_combined_score(revised_result)
        candidates.append(revised_result)

        print("Revised candidate:")
        print(f"  Monomer 1: {revised_result.get('monomer_1')}")
        print(f"  Monomer 2: {revised_result.get('monomer_2')}")
        print(f"  Tg error: {revised_result['property_details']['dtg']}")
        print(f"  Er error: {revised_result['property_details']['der']}")
        print(f"  Score: {revised_score:.4f}")

        if revised_score < best_score:
            best_result = revised_result
            best_score = revised_score
            print("  -> New best candidate selected")
        else:
            print("  -> Revision did not improve overall score")

        if is_within_tolerance(best_result):
            print("Stopping early: best candidate is within tolerance.")
            break

    print("\n=== Final Best Candidate ===")
    print(f"Monomer 1: {best_result.get('monomer_1')}")
    print(f"Monomer 2: {best_result.get('monomer_2')}")
    print(f"Tg error: {best_result['property_details']['dtg']}")
    print(f"Er error: {best_result['property_details']['der']}")
    print(f"Best score: {best_score:.4f}")

    print("--------------------------------")
    print(best_result)
    print("--------------------------------")

    try:
        log_dir = Path("Evaluations") / "results"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "router_evaluations.json"

        record = {
            "initial_result": initial_result,
            "final_best_result": best_result,
            "all_candidates": candidates,
        }

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        print(f"Saved evaluation record to {log_path}")
    except Exception as e:
        print(f"Failed to save evaluation record: {e}")

    return best_result

