# import json
# from pathlib import Path
# from typing import Any, Dict, List, Optional

# from .path_setup import ensure_generator_on_syspath
# from .scoring import compute_combined_score_single, is_within_tolerance_single
# from .llm_revision import process_llm_revision
# from .request_builder_single import build_property_revision_request

# ensure_generator_on_syspath()

# from Generator.singel_property_constraint import read_json_from_file, evaluate_property_constraints  # noqa: E402
# from LLM_Reviser.llm_call_for_single import call_llm_reviser
# # noqa: E402


# def _resolve_focus_property(result: Dict[str, Any]) -> str:
#     focus = str(result.get("focus_property", "")).lower()
#     return focus if focus in {"tg", "er"} else "tg"


# def _print_candidate(result: Dict[str, Any], label: str = "Candidate"):
#     print(f"{label}:")
#     print(f"  Monomer 1: {result.get('monomer_1')}")
#     print(f"  Monomer 2: {result.get('monomer_2')}")
#     print(f"  Property details: {result['property_details']}")
#     print(f"  Score: {compute_combined_score_single(result):.4f}")


# def _candidate_revision_loop(
#     initial_result: Dict[str, Any],
#     max_iterations: int = 3
# ) -> (Dict[str, Any], List[Dict[str, Any]]):
#     if "focus_property" not in initial_result:
#         initial_result["focus_property"] = _resolve_focus_property(initial_result)
#     active_focus = _resolve_focus_property(initial_result)
#     best_result = initial_result
#     best_score = compute_combined_score_single({**best_result, "focus_property": active_focus})
#     candidates: List[Dict[str, Any]] = [initial_result]

#     if not initial_result.get("is_agent_call_needed", False):
#         print("Agent call not needed")
#         print("--------------------------------")
#         print(best_result)

#     _print_candidate(best_result, "Original candidate")
#     print("Agent call needed")
#     print("--------------------------------")

#     for step in range(max_iterations):
#         print(f"\n--- Revision iteration {step + 1} ---")
#         focus_property = _resolve_focus_property(best_result)
#         active_focus = focus_property
#         request = build_property_revision_request(best_result, focus_property=active_focus)
#         raw_response = call_llm_reviser(request)

#         print("LLM reviser raw response:")
#         print(raw_response)

#         processed = process_llm_revision(raw_response, best_result)

#         if not processed["accepted"]:
#             print("Revision rejected:")
#             print(processed["reason"])

#             rejected_record = {
#                 "status": processed.get("status"),
#                 "accepted": False,
#                 "reason": processed.get("reason"),
#                 "raw_response": processed.get("raw_response"),
#                 "repair_response": processed.get("repair_response"),
#                 "parsed_candidate": processed.get("parsed_candidate"),
#                 "validation": processed.get("validation"),
#             }
#             candidates.append(rejected_record)
#             continue

#         revised_result = processed["evaluated_result"]
#         # Preserve single-property focus across iterations for scoring/stopping.
#         revised_result["focus_property"] = active_focus
#         revised_score = compute_combined_score_single({**revised_result, "focus_property": active_focus})
#         candidates.append(revised_result)

#         print("Revised candidate:")
#         print(f"  Monomer 1: {revised_result.get('monomer_1')}")
#         print(f"  Monomer 2: {revised_result.get('monomer_2')}")
#         print(f"  Tg error: {revised_result['property_details']['dtg']}")
#         print(f"  Er error: {revised_result['property_details']['der']}")
#         print(f"  Score: {revised_score:.4f}")

#         if revised_score < best_score:
#             best_result = revised_result
#             best_result["focus_property"] = active_focus
#             best_score = revised_score
#             print("  -> New best candidate selected")
#         else:
#             print("  -> Revision did not improve overall score")

#         if is_within_tolerance_single({**best_result, "focus_property": active_focus}):
#             print("Stopping early: best candidate is within tolerance.")
#             break

#     print("\n=== Final Best Candidate ===")
#     print(f"Monomer 1: {best_result.get('monomer_1')}")
#     print(f"Monomer 2: {best_result.get('monomer_2')}")
#     print(f"Tg error: {best_result['property_details']['dtg']}")
#     print(f"Er error: {best_result['property_details']['der']}")
#     print(f"Best score: {best_score:.4f}")

#     print("--------------------------------")
#     print(best_result)
#     print("--------------------------------")

#     return best_result, candidates


# def _log_and_return(initial_result: Dict[str, Any], best_result: Dict[str, Any], candidates: List[Dict[str, Any]]):
#     try:
#         log_dir = Path("Evaluations") / "results"
#         log_dir.mkdir(parents=True, exist_ok=True)
#         log_path = log_dir / "router_evaluations.json"

#         record = {
#             "initial_result": initial_result,
#             "final_best_result": best_result,
#             "all_candidates": candidates,
#         }

#         existing_records: List[Dict[str, Any]] = []
#         if log_path.exists():
#             with open(log_path, "r", encoding="utf-8") as f:
#                 existing_content = f.read().strip()
#                 if existing_content:
#                     parsed_content = json.loads(existing_content)
#                     if isinstance(parsed_content, list):
#                         existing_records = parsed_content
#                     elif isinstance(parsed_content, dict):
#                         existing_records = [parsed_content]

#         existing_records.append(record)

#         with open(log_path, "w", encoding="utf-8") as f:
#             json.dump(existing_records, f, ensure_ascii=False, indent=2)

#         print(f"Saved evaluation record to {log_path}")
#     except Exception as e:
#         print(f"Failed to save evaluation record: {e}")

#     return best_result


# def evaluate(
#     input_json_path: str = str(Path("Evaluations") / "prompts" / "property_prompt_sample_100.json"),
#     max_iterations: int = 3,
# ) -> Optional[Dict[str, Any]]:
#     result = read_json_from_file(input_json_path)
#     if result is None:
#         print("No valid result returned from read_json_from_file.")
#         return None

#     best_result, candidates = _candidate_revision_loop(result, max_iterations)
#     return _log_and_return(result, best_result, candidates)


# def best_candidate_for_property_constraints(
#     monomer_1: str,
#     monomer_2: str,
#     target_tg: float,
#     target_er: float,
#     tol_tg: float,
#     tol_er: float,
#     prompt: str,
#     max_iterations: int = 3,
# ) -> Optional[Dict[str, Any]]:
#     result = evaluate_property_constraints(
#         monomer_1,
#         monomer_2,
#         target_tg,
#         target_er,
#         tol_tg,
#         tol_er,
#         prompt,
#     )
#     if result is None:
#         print("No valid result returned from read_json_from_file.")
#         return None

#     best_result, candidates = _candidate_revision_loop(result, max_iterations)
#     return _log_and_return(result, best_result, candidates)
