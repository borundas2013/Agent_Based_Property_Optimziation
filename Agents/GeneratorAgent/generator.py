"""
Public entrypoint for the generator agent. Other modules should import from here.

Implementation is split across ``paths``, ``constants``, ``evaluation``, ``llm``,
``results``, ``serialization``, and ``agent_loop``.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

import paths  # noqa: F401

from feedback.feedback import (
    ISSUE_CHEMICAL_INVALID,
    ISSUE_GROUP1_MISSING,
    ISSUE_GROUP2_MISSING,
    ISSUE_PROPERTY_PREDICTION_FAILED,
    ISSUE_REACTION_INCOMPATIBLE,
    ISSUE_REQUESTED_GROUPS_FAILED,
    check_property,
    generate_feedback,
)

from agent_loop import run_agent_loop
from constants import STRUCTURAL_ISSUE_CODES
from evaluation import (
    evaluate_sample,
    final_property_prediction,
    rank_tuple,
    safe_float,
    threshold_notes,
)
from llm import call_llm, client, generate_monomers
from results import (
    build_final_result,
    build_slim_run_payload,
    compact_sample_for_save,
)
from serialization import parse_monomer_json, save_run_to_json, to_jsonable

__all__ = [
    "ISSUE_CHEMICAL_INVALID",
    "ISSUE_GROUP1_MISSING",
    "ISSUE_GROUP2_MISSING",
    "ISSUE_PROPERTY_PREDICTION_FAILED",
    "ISSUE_REACTION_INCOMPATIBLE",
    "ISSUE_REQUESTED_GROUPS_FAILED",
    "check_property",
    "generate_feedback",
    "STRUCTURAL_ISSUE_CODES",
    "call_llm",
    "client",
    "generate_monomers",
    "run_agent_loop",
    "build_slim_run_payload",
    "save_run_to_json",
    "parse_monomer_json",
    "to_jsonable",
    "evaluate_sample",
    "final_property_prediction",
    "rank_tuple",
    "safe_float",
    "threshold_notes",
    "build_final_result",
    "compact_sample_for_save",
]


if __name__ == "__main__":
    target_tg = 150
    target_er = 75
    group1 = "C1OC1"
    group2 = "NC"

    _out_dir = os.path.join(os.path.dirname(__file__), "outputs")
    _stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _json_path = os.path.join(_out_dir, f"generator_run_{_stamp}.json")

    output = run_agent_loop(
        target_tg=target_tg,
        target_er=target_er,
        group1=group1,
        group2=group2,
        max_iters=3,
        model="gpt-5-mini",
        output_json_path=_json_path,
    )

    print("\n=== SAVED SHAPE (same as JSON file) ===")
    print(json.dumps(output["slim_save"], indent=2))

    if output.get("saved_json_path"):
        print(f"\nSaved JSON: {output['saved_json_path']}")

    print(f"\nStopped reason: {output['stopped_reason']}")
