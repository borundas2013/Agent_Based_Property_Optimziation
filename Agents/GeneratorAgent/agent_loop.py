from __future__ import annotations

import paths  # noqa: F401
from datetime import datetime
from typing import Any, Dict, List, Optional

from evaluation import evaluate_sample, rank_tuple
from feedback.feedback import generate_feedback
from llm import generate_monomers
from results import build_final_result, build_slim_run_payload
from serialization import save_run_to_json
from router.evaluate import best_candidate_for_property_constraints


def run_agent_loop(
    target_tg: Optional[float],
    target_er: Optional[float],
    group1: Optional[str],
    group2: Optional[str],
    max_iters: int = 3,
    model: str = "gpt-5-mini",
    output_json_path: Optional[str] = None,
) -> Dict[str, Any]:
    candidates: List[Dict[str, Any]] = []

    result = generate_monomers(
        target_tg=target_tg,
        target_er=target_er,
        group1=group1,
        group2=group2,
        prev_m1=None,
        prev_m2=None,
        feedback_text=None,
        model=model,
    )

    prev_m1 = result["monomer1"]
    prev_m2 = result["monomer2"]
    candidates.append({"label": "initial", "llm_result": result})

    stopped_reason = f"Reached max iterations ({max_iters})"

    for i in range(1, max_iters + 1):
        feedback_result = generate_feedback(
            monomer_1=prev_m1,
            monomer_2=prev_m2,
            group1=group1,
            group2=group2,
            target_tg=target_tg,
            target_er=target_er,
        )
        # Same pair as candidates[i - 1]; reuse in evaluate_sample (no second generate_feedback).
        candidates[i - 1]["precomputed_feedback"] = feedback_result

        if not feedback_result.get("needs_revision", True):
            stopped_reason = "No revision needed"
            break

        feedback_text = feedback_result.get("feedback_text", "")
        revised_result = generate_monomers(
            target_tg=target_tg,
            target_er=target_er,
            group1=group1,
            group2=group2,
            prev_m1=prev_m1,
            prev_m2=prev_m2,
            feedback_text=feedback_text,
            model=model,
        )

        prev_m1 = revised_result["monomer1"]
        prev_m2 = revised_result["monomer2"]
        candidates.append({"label": f"revision_{i}", "llm_result": revised_result})

    # After the last revision with needs_revision True, we never run feedback on the final pair in-loop.
    if candidates[-1].get("precomputed_feedback") is None:
        candidates[-1]["precomputed_feedback"] = generate_feedback(
            monomer_1=prev_m1,
            monomer_2=prev_m2,
            group1=group1,
            group2=group2,
            target_tg=target_tg,
            target_er=target_er,
        )

    evaluated: List[Dict[str, Any]] = []
    for c in candidates:
        evaluated.append(
            evaluate_sample(
                label=c["label"],
                llm_result=c["llm_result"],
                target_tg=target_tg,
                target_er=target_er,
                group1=group1,
                group2=group2,
                precomputed_feedback=c.get("precomputed_feedback"),
            )
        )

    initial_sample = next(e for e in evaluated if e["label"] == "initial")
    best_sample = min(evaluated, key=rank_tuple)

    within = (best_sample.get("property_prediction_full") or {}).get(
        "within_property_tolerance"
    )
    if within is not None and not bool(within):
        best_candidate_for_property_constraints(
            monomer_1=best_sample["monomer1"],
            monomer_2=best_sample["monomer2"],
            target_tg=target_tg,
            target_er=target_er,
            tol_tg=10,#tol_tg,
            tol_er=5,#tol_er,
            prompt="SSSSS",
        )

        print(
            "[GeneratorAgent] Best sample is not within Tg/Er tolerance; "
            "separate agent calls are needed.",
            flush=True,
        )

    ranking_meta = {
        "criteria": (
            "Prefer: (1) chemical validity, (2) reaction compatibility for crosslinking, "
            "(3) requested group placement; then (4) minimize Tg/Er absolute errors (dtg, der) "
            "when property prediction is available."
        ),
        "best_label": best_sample["label"],
        "initial_label": "initial",
        "all_candidate_labels": [e["label"] for e in evaluated],
    }

    prop_best = best_sample.get("property_prediction_full")
    final_result = build_final_result(
        best_sample["monomer1"],
        best_sample["monomer2"],
        best_sample["reason"],
        prop_best,
    )
    final_result["chosen_as_best_label"] = best_sample["label"]

    payload = {
        "meta": {
            "target_tg": target_tg,
            "target_er": target_er,
            "group1": group1,
            "group2": group2,
            "model": model,
            "max_iters": max_iters,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
        },
        "initial": initial_sample,
        "best": best_sample,
        "ranking": ranking_meta,
        "final_result": final_result,
        "stopped_reason": stopped_reason,
    }
    slim = build_slim_run_payload(
        initial_sample,
        best_sample,
        target_tg=target_tg,
        target_er=target_er,
        group1=group1,
        group2=group2,
    )
    saved_path = None
    if output_json_path:
        saved_path = save_run_to_json(slim, output_json_path)
    return {
        **payload,
        "saved_json_path": saved_path,
        "slim_save": slim,
    }
