import os
import sys

# Ensure the Generator directory is on sys.path so that
# imports inside ConstraintsChecking (like `from template import *`)
# can resolve correctly without modifying inner files.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATOR_DIR = os.path.join(BASE_DIR, "Generator")
if GENERATOR_DIR not in sys.path:
    sys.path.insert(0, GENERATOR_DIR)

from Generator.ConstraintsChecking import check_tg_er_properties

from Tool_based_reviser.rules_apply import refine_and_evaluate_tg
from Tool_based_reviser.decision_rules import decide_tg_rules, print_tg_decision

def apply_rule_and_predict(m1, m2, rule_name):
    """
    Apply a revision rule (using refine_and_evaluate_tg for this example) to the given monomer pair.
    Returns a result object with required fields:
        - success
        - modified_monomer_1
        - modified_monomer_2
        - new_predicted_tg
    """
    # Compute current predicted Tg for this pair, to pass into the refinement logic.
    local_predicted_tg = tg_predictor(m1, m2)

    refinement = refine_and_evaluate_tg(
        monomer_1=m1,
        monomer_2=m2,
        predicted_tg=local_predicted_tg,
        target_tg=target_tg,
        tg_predictor=tg_predictor,
        threshold=tol_tg,
        top_k=1,
    )
    # For a more precise approach, you would look for the correct rule_name, but for this top-of-file fix this suffices.
    class Result:
        def __init__(self, refinement):
            self.success = (
                refinement.modified_monomer_1 != m1 or refinement.modified_monomer_2 != m2
            )
            self.modified_monomer_1 = refinement.modified_monomer_1
            self.modified_monomer_2 = refinement.modified_monomer_2
            self.new_predicted_tg = getattr(refinement, "new_predicted_tg", None) or refinement.original_predicted_tg
    return Result(refinement)

if __name__ == "__main__":
    # Define an example initial result with target and tolerance information

    monomer_1 = "CC(C)(c2ccc(OCC1CO1)cc2)c4ccc(OCC3CO3)cc4"
    monomer_2 = "CC(N)COCC(C)OCC(C)OCC(C)OCC(C)OCC(C)N"

    target_tg = 130
    target_er = 28
    tol_tg = 10.0
    tol_er = 10.0

    property_result = check_tg_er_properties(
        monomer_1, monomer_2, target_tg, target_er, tol_tg, tol_er
    )
    current_m1 = monomer_1
    current_m2 = monomer_2
    current_tg = float(property_result["predicted_tg"])

    predicted_tg = float(property_result["predicted_tg"])
    predicted_er = float(property_result["predicted_er"])

    def make_tg_predictor(target_tg: float, target_er: float, tol_tg: float, tol_er: float):
        def predictor(m1: str, m2: str) -> float:
            prop_result = check_tg_er_properties(m1, m2, target_tg, target_er, tol_tg, tol_er)
            return float(prop_result["predicted_tg"])
        return predictor

    tg_predictor = make_tg_predictor(target_tg, target_er, tol_tg, tol_er)

    max_iterations = 10  # define this, was missing
    threshold = tol_tg   # assign threshold variable, using tol_tg

    for step in range(max_iterations):
        decision = decide_tg_rules(current_m1, current_m2, current_tg, target_tg)

        if decision.direction == "keep":
            print(f"Direction is 'keep' after {step} steps. Stopping refinement.")
            break

        improved = False
        best_candidate = None
        best_error = abs(target_tg - current_tg)

        for suggestion in getattr(decision, "suggestions", []):
            candidate = apply_rule_and_predict(
                current_m1, current_m2, suggestion.rule_name
            )

            if not getattr(candidate, "success", False):
                continue

            candidate_error = abs(target_tg - candidate.new_predicted_tg)

            if candidate_error < best_error:
                best_error = candidate_error
                best_candidate = candidate
                improved = True

        if not improved or best_candidate is None:
            print(f"No improvement found at step {step}, stopping.")
            break

        current_m1 = best_candidate.modified_monomer_1
        current_m2 = best_candidate.modified_monomer_2
        current_tg = best_candidate.new_predicted_tg

        if abs(target_tg - current_tg) <= threshold:
            print(f"Tg refined to within threshold after {step+1} steps. Stopping.")
            
