"""
Property and constraint utilities for TSMP monomer pairs.

This module was extracted from the original `ConstraintsChecking.py` to
provide a clearer, PEP8-compliant name and a more organized layout.
"""

import json
import os
import random
import sys
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from template import *
from constraints.chemical_validity import ChemicalValidityCheck
from constraints.group_validity import GroupCheck
from constraints.monomer_extraction import *
from Predictor_Agent.property_check.property_checker import PropertyChecker
from extraction import extract_monomer_smiles

# ---------------------------------------------------------------------
# Environment / configuration
# ---------------------------------------------------------------------

# Ensure the Agents directory is on sys.path so we can import Predictor_Agent
AGENTS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if AGENTS_ROOT not in sys.path:
    sys.path.insert(0, AGENTS_ROOT)

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_ID = os.getenv("FINETUNED_MODEL_ID")

TOL_TG = 10
TOL_ER = 10

chemical_validity_check = ChemicalValidityCheck()
group_validity_check = GroupCheck()


# ---------------------------------------------------------------------
# JSON loading helper
# ---------------------------------------------------------------------

def read_json_from_file(filename: str) -> Any:
    """
    Read JSON data from a file (relative to the Agents root) and print its length.

    Returns the loaded JSON object, or None if nothing matched the embedded
    property selection logic.
    """
    if not filename.endswith(".json"):
        filename += ".json"

    eval_dir = os.path.join(os.path.dirname(__file__), "..")
    file_path = os.path.join(eval_dir, filename)

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        length = len(data)
        print(f"Length of list loaded from {file_path}: {length}")
    except TypeError:
        # Data has no length (e.g., int, float, None); just show its type.
        print(f"Loaded data from {file_path} (type: {type(data).__name__})")

    if isinstance(data, list):
        processed: list = []
        for idx, item in enumerate(data):
            if isinstance(item, dict):
                prompt = item["prompt"]
                target_tg = item["target_tg"]
                target_er = item["target_er"]

                if target_tg is not None and target_er is not None:
                    response = generate_sample_data(prompt)

                    smiles = extract_monomer_smiles(response)

                    monomer_1 = smiles[0]
                    monomer_2 = smiles[1]

                    chemical_validity, smiles_1, smiles_2 = (
                        chemical_validity_check.check_chemical_validity(
                            monomer_1, monomer_2
                        )
                    )
                    if smiles_1:
                        monomer_1 = smiles_1
                    if smiles_2:
                        monomer_2 = smiles_2

                    group_validity = group_validity_check.check_exact_group_consistency(
                        monomer_1, monomer_2, None, None
                    )

                    if not chemical_validity:
                        print(f"Sample {idx}: chemical validity failed, skipping.")
                        continue

                    property_details = check_tg_er_properties(
                        monomer_1,
                        monomer_2,
                        target_tg,
                        target_er,
                        TOL_TG,
                        TOL_ER,
                    )
                    dtg = float(property_details.get("dtg"))
                    der = float(property_details.get("der"))

                    needs_agent = dtg > TOL_TG or der > TOL_ER
                    processed.append(
                        {
                            "sample_index": idx,
                            "prompt": prompt,
                            "target_tg": target_tg,
                            "target_er": target_er,
                            "monomer_1": monomer_1,
                            "monomer_2": monomer_2,
                            "chemical_validity": chemical_validity,
                            "group_validity": group_validity,
                            "property_details": property_details,
                            "is_agent_call_needed": needs_agent,
                        }
                    )
                    print(f"Sample {idx}: processed (agent_needed={needs_agent}).")
                else:
                    print(f"No target_tg or target_er found for item {idx}")
                

        if processed:
            return processed
        print("No list items were successfully processed (all skipped or invalid).")
        return []

    else:
        print("Loaded JSON is not a list, full data:")

    return data


def evaluate_property_constraints(
    monomer_1: str,
    monomer_2: str,
    target_tg: float,
    target_er: float,
    tol_tg: float,
    tol_er: float,
    prompt: str,
):
    chemical_validity = chemical_validity_check.check_chemical_validity(
        monomer_1, monomer_2
    )
    group_validity = group_validity_check.check_exact_group_consistency(
        monomer_1, monomer_2, None, None
    )

    property_details = check_tg_er_properties(
        monomer_1,
        monomer_2,
        target_tg,
        target_er,
        TOL_TG,
        TOL_ER,
    )
    dtg = float(property_details.get("dtg"))
    der = float(property_details.get("der"))

    is_agent_call_needed = dtg > TOL_TG or der > TOL_ER

    if is_agent_call_needed:
        return {
            "target_tg": target_tg,
            "target_er": target_er,
            "monomer_1": monomer_1,
            "monomer_2": monomer_2,
            "chemical_validity": chemical_validity,
            "group_validity": group_validity,
            "property_details": property_details,
            "is_agent_call_needed": True,
        }
    else:
        return {
            "target_tg": target_tg,
            "target_er": target_er,
            "monomer_1": monomer_1,
            "monomer_2": monomer_2,
            "property_details": property_details,
            "is_agent_call_needed": False,
        }
# ---------------------------------------------------------------------

def check_tg_er_properties(
    monomer_1: str,
    monomer_2: str,
    target_tg: float,
    target_er: float,
    tol_tg: float,
    tol_er: float,
):
    """Convenience wrapper around `check_property` used throughout the agents."""
    result = check_property(
        monomer_1,
        monomer_2,
        target_tg,
        target_er,
        tol_tg,
        tol_er,
    )
    return result


def check_property(
    monomer_1: str,
    monomer_2: str,
    target_tg: float,
    target_er: float,
    tol_tg: float | None = None,
    tol_er: float | None = None,
):
    """
    Sweep composition ratios and use PropertyChecker to find the best Tg/Er match.

    Returns
    -------
    dict | None
        Best result dictionary from PropertyChecker, augmented with
        the chosen ratio_1 and ratio_2. Returns None if all evaluations fail.
    """
    property_checker = PropertyChecker()

    # Use checker defaults if tolerances are not provided
    tol_tg = float(tol_tg) if tol_tg is not None else float(property_checker.tol_tg)
    tol_er = float(tol_er) if tol_er is not None else float(property_checker.tol_er)

    best_result: dict | None = None
    best_score: tuple[float, float] | None = None

    # Sweep ratio_1 from 0.1 → 0.9 (step 0.1); ratio_2 = 1 - ratio_1
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
            # Skip this ratio setting if model fails
            continue

        dtg = float(result.get("dtg"))
        der = float(result.get("der"))

        # Prefer dtg/der close to or below tolerances.
        over_tg = max(dtg - tol_tg, 0.0)
        over_er = max(der - tol_er, 0.0)
        penalty = over_tg + over_er
        tie_break = dtg + der
        score_tuple = (penalty, tie_break)

        if (best_score is None) or (score_tuple < best_score):
            best_score = score_tuple
            # Record the best result and ratios used
            best_result = {
                **result,
                "ratio_1": ratio_1,
                "ratio_2": ratio_2,
            }

    return best_result


# ---------------------------------------------------------------------
# Optional: sample data generation via LLM
# ---------------------------------------------------------------------

def generate_sample_data(prompt: str) -> str:
    """
    Use the fine‑tuned OpenAI model to generate sample data for a prompt/target pair.
    """
    messages = [
        {"role": "system", "content": system_prompt_template},
        {"role": "user", "content": prompt},
    ]

    client = OpenAI(api_key=API_KEY)
    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=messages,
        temperature=0.0,
        max_tokens=300,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    result = read_json_from_file("Evaluations\\prompts\\property_prompt_sample_100.json")
    print(result)

