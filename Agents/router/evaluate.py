import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .path_setup import ensure_generator_on_syspath
from .scoring import compute_combined_score, is_within_tolerance
from .llm_revision import process_llm_revision
from .request_builder import build_property_revision_request

ensure_generator_on_syspath()

from Generator.property_constraints import read_json_from_file, evaluate_property_constraints  # noqa: E402
from LLM_Reviser.opensource_llm_refinement import call_llm_reviser as call_llm_reviser_opensource
from LLM_Reviser.llm_call_for_both import call_llm_reviser
# noqa: E402


def _print_candidate(result: Dict[str, Any], label: str = "Candidate"):
    print(f"{label}:")
    print(f"  Monomer 1: {result.get('monomer_1')}")
    print(f"  Monomer 2: {result.get('monomer_2')}")
    print(f"  Property details: {result['property_details']}")
    print(f"  Score: {compute_combined_score(result):.4f}")


def _candidate_revision_loop(
    initial_result: Dict[str, Any],
    max_iterations: int = 3
) -> (Dict[str, Any], List[Dict[str, Any]]):
    best_result = initial_result
    best_score = compute_combined_score(best_result)
    candidates: List[Dict[str, Any]] = [initial_result]

    if not initial_result.get("is_agent_call_needed", False):
        print("Agent call not needed")
        print("--------------------------------")
        print(best_result)

    _print_candidate(best_result, "Original candidate")
    print("Agent call needed")
    print("--------------------------------")

    for step in range(max_iterations):
        print(f"\n--- Revision iteration {step + 1} ---")
        request = build_property_revision_request(best_result, focus_property="both")
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

    return best_result, candidates


def _next_sl(csv_path: Path) -> int:
    if not csv_path.exists():
        return 1
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return 1
    return len(rows)


def _log_and_return(initial_result: Dict[str, Any], best_result: Dict[str, Any], candidates: List[Dict[str, Any]]):
    try:
        log_dir = Path("Evaluations") / "results"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "router_evaluations.csv"

        init_pd = initial_result.get("property_details", {}) or {}
        fin_pd = best_result.get("property_details", {}) or {}

        def _f(key: str, d: Dict[str, Any]) -> str:
            v = d.get(key)
            return "" if v is None else str(v)

        sl = _next_sl(log_path)
        rejected_steps = [
            c for c in candidates[1:]
            if isinstance(c, dict) and c.get("accepted") is False
        ]
        revision_steps = [
            c for c in candidates[1:]
            if isinstance(c, dict)
            and "property_details" in c
            and c.get("monomer_1") is not None
            and c.get("accepted", True) is not False
        ]

        row = {
            "SL": sl,
            "prompt": initial_result.get("prompt", ""),
            "target_tg": _f("target_tg", initial_result) or _f("tg_target", init_pd),
            "target_er": _f("target_er", initial_result) or _f("er_target", init_pd),
            "initial_monomer_1": initial_result.get("monomer_1", ""),
            "initial_monomer_2": initial_result.get("monomer_2", ""),
            "initial_predicted_tg": init_pd.get("predicted_tg", ""),
            "initial_predicted_er": init_pd.get("predicted_er", ""),
            "initial_dtg": init_pd.get("dtg", ""),
            "initial_der": init_pd.get("der", ""),
            "initial_tol_tg": init_pd.get("tol_tg", ""),
            "initial_tol_er": init_pd.get("tol_er", ""),
            "initial_ratio_1": init_pd.get("ratio_1", ""),
            "initial_ratio_2": init_pd.get("ratio_2", ""),
            "final_monomer_1": best_result.get("monomer_1", ""),
            "final_monomer_2": best_result.get("monomer_2", ""),
            "final_predicted_tg": fin_pd.get("predicted_tg", ""),
            "final_predicted_er": fin_pd.get("predicted_er", ""),
            "final_dtg": fin_pd.get("dtg", ""),
            "final_der": fin_pd.get("der", ""),
            "final_tol_tg": fin_pd.get("tol_tg", ""),
            "final_tol_er": fin_pd.get("tol_er", ""),
            "final_ratio_1": fin_pd.get("ratio_1", ""),
            "final_ratio_2": fin_pd.get("ratio_2", ""),
            "revision_summary": best_result.get("revision_summary", ""),
           
        }

        fieldnames = list(row.keys())
        file_exists = log_path.exists()
        with open(log_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

        print(f"Saved evaluation record to {log_path}")
    except Exception as e:
        print(f"Failed to save evaluation record: {e}")

    return best_result


def evaluate(
    input_json_path: str = str(Path("Evaluations") / "prompts" / "property_prompt_sample_100.json"),
    max_iterations: int = 3,
) -> Optional[Any]:
    result = read_json_from_file(input_json_path)
    if result is None:
        print("No valid result returned from read_json_from_file.")
        return None

    if isinstance(result, list):
        if not result:
            print("No samples were processed from the JSON list (all skipped or empty).")
            return None
        finals: List[Dict[str, Any]] = []
        for i, sample in enumerate(result):
            print(f"\n{'=' * 60}\nBatch sample {i + 1}/{len(result)} (index={sample.get('sample_index', i)})\n{'=' * 60}")
            best_result, candidates = _candidate_revision_loop(sample, max_iterations)
            finals.append(_log_and_return(sample, best_result, candidates))
        return finals

    best_result, candidates = _candidate_revision_loop(result, max_iterations)
    return _log_and_return(result, best_result, candidates)


def best_candidate_for_property_constraints(
    monomer_1: str,
    monomer_2: str,
    target_tg: float,
    target_er: float,
    tol_tg: float,
    tol_er: float,
    prompt: str,
    max_iterations: int = 3,
) -> Optional[Dict[str, Any]]:
    result = evaluate_property_constraints(
        monomer_1,
        monomer_2,
        target_tg,
        target_er,
        tol_tg,
        tol_er,
        prompt,
    )
    if result is None:
        print("No valid result returned from read_json_from_file.")
        return None

    best_result, candidates = _candidate_revision_loop(result, max_iterations)
    return _log_and_return(result, best_result, candidates)


def _property_band(predicted: float, target: float, tol: float) -> str:
    """
    How the prediction sits vs target given symmetric tolerance ±tol.
    - within: |predicted - target| <= tol
    - above: predicted > target + tol (too high vs target)
    - below: predicted < target - tol (too low vs target)
    """
    if abs(predicted - target) <= tol:
        return "within"
    if predicted > target + tol:
        return "above"
    return "below"


def _pct(count: int, total: int) -> str:
    return f"{count} ({count / total:.1%})" if total else "0 (n/a)"


def _print_tolerance_breakdown(title: str, n: int, rows: List[Dict[str, Any]], prefix: str) -> None:
    """prefix: 'initial' or 'final' for dict keys like initial_tg_band."""
    tg_w = sum(1 for x in rows if x[f"{prefix}_tg_band"] == "within")
    tg_a = sum(1 for x in rows if x[f"{prefix}_tg_band"] == "above")
    tg_b = sum(1 for x in rows if x[f"{prefix}_tg_band"] == "below")
    er_w = sum(1 for x in rows if x[f"{prefix}_er_band"] == "within")
    er_a = sum(1 for x in rows if x[f"{prefix}_er_band"] == "above")
    er_b = sum(1 for x in rows if x[f"{prefix}_er_band"] == "below")
    both_within_key = "within_tol_initial" if prefix == "initial" else "within_tol_final"
    n_both = sum(1 for x in rows if x[both_within_key])
    n_out = n - n_both

    print(title)
    print(
        f"  Both properties within tolerance (Tg AND Er): {_pct(n_both, n)}"
    )
    print(
        f"  At least one property outside tolerance: {_pct(n_out, n)}"
    )
    print("  Per property (each sample counted once; within / too high / too low vs target±tol):")
    print(f"    Tg:  within {_pct(tg_w, n)} | too high {_pct(tg_a, n)} | too low {_pct(tg_b, n)}")
    print(f"    Er:  within {_pct(er_w, n)} | too high {_pct(er_a, n)} | too low {_pct(er_b, n)}")
    print()


def evaluate_improvement_from_csv(
    csv_path: str = str(Path("Evaluations") / "results" / "router_evaluations.csv"),
):
    """
    Read router_evaluations.csv and summarize how often initial vs final predictions
    sit within tolerance or outside (too high / too low vs target), plus revision deltas.
    """
    improvements: List[Dict[str, Any]] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                sample = {
                    "target_tg": float(row["target_tg"]),
                    "target_er": float(row["target_er"]),
                    "initial_predicted_tg": float(row["initial_predicted_tg"]),
                    "initial_predicted_er": float(row["initial_predicted_er"]),
                    "final_predicted_tg": float(row["final_predicted_tg"]),
                    "final_predicted_er": float(row["final_predicted_er"]),
                    "initial_tol_tg": float(row["initial_tol_tg"]),
                    "initial_tol_er": float(row["initial_tol_er"]),
                    "final_tol_tg": float(row.get("final_tol_tg", row["initial_tol_tg"])),
                    "final_tol_er": float(row.get("final_tol_er", row["initial_tol_er"])),
                }
            except Exception as e:
                print(f"[WARN] Skipping row due to missing/invalid values: {e}")
                continue

            initial_dtg = abs(sample["initial_predicted_tg"] - sample["target_tg"])
            initial_der = abs(sample["initial_predicted_er"] - sample["target_er"])
            final_dtg = abs(sample["final_predicted_tg"] - sample["target_tg"])
            final_der = abs(sample["final_predicted_er"] - sample["target_er"])

            within_tol_initial = (
                initial_dtg <= sample["initial_tol_tg"] and initial_der <= sample["initial_tol_er"]
            )
            within_tol_final = (
                final_dtg <= sample["final_tol_tg"] and final_der <= sample["final_tol_er"]
            )

            tg_improved = final_dtg < initial_dtg
            er_improved = final_der < initial_der
            both_improved = tg_improved and er_improved

            initial_tg_band = _property_band(
                sample["initial_predicted_tg"], sample["target_tg"], sample["initial_tol_tg"]
            )
            initial_er_band = _property_band(
                sample["initial_predicted_er"], sample["target_er"], sample["initial_tol_er"]
            )
            final_tg_band = _property_band(
                sample["final_predicted_tg"], sample["target_tg"], sample["final_tol_tg"]
            )
            final_er_band = _property_band(
                sample["final_predicted_er"], sample["target_er"], sample["final_tol_er"]
            )

            improvements.append(
                {
                    "SL": row["SL"],
                    "tg_improved": tg_improved,
                    "er_improved": er_improved,
                    "both_improved": both_improved,
                    "within_tol_initial": within_tol_initial,
                    "within_tol_final": within_tol_final,
                    "initial_dtg": initial_dtg,
                    "initial_der": initial_der,
                    "final_dtg": final_dtg,
                    "final_der": final_der,
                    "initial_tg_band": initial_tg_band,
                    "initial_er_band": initial_er_band,
                    "final_tg_band": final_tg_band,
                    "final_er_band": final_er_band,
                }
            )

    n = len(improvements)
    if n == 0:
        print("No samples analyzed.")
        return []

    n_tg_improved = sum(x["tg_improved"] for x in improvements)
    n_er_improved = sum(x["er_improved"] for x in improvements)
    n_both_improved = sum(x["both_improved"] for x in improvements)
    n_newly_solved = sum(
        (not x["within_tol_initial"]) and x["within_tol_final"] for x in improvements
    )
    n_still_ok = sum(x["within_tol_initial"] and x["within_tol_final"] for x in improvements)
    n_regressed = sum(x["within_tol_initial"] and (not x["within_tol_final"]) for x in improvements)

    print(f"Samples analyzed: {n}\n")
    _print_tolerance_breakdown("--- Initial prediction (before revision) ---", n, improvements, "initial")
    _print_tolerance_breakdown("--- After final revision ---", n, improvements, "final")

    print("--- Revision effect (error magnitude) ---")
    print(f"  Tg error decreased: {_pct(n_tg_improved, n)}")
    print(f"  Er error decreased: {_pct(n_er_improved, n)}")
    print(f"  Both Tg and Er errors decreased: {_pct(n_both_improved, n)}")
    print()
    print("--- Joint tolerance transitions ---")
    print(
        f"  Newly within tolerance (was outside, now both within): {_pct(n_newly_solved, n)}"
    )
    print(
        f"  Stayed within tolerance (initially ok, still ok): {_pct(n_still_ok, n)}"
    )
    print(
        f"  Regressed (was within, now outside): {_pct(n_regressed, n)}"
    )

    return improvements