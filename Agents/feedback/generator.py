from __future__ import annotations

from typing import Any, Dict, List, Optional

from Generator.constraints.chemical_validity import ChemicalValidityCheck
from Generator.constraints.group_validity import GroupCheck
from Generator.constraints.groups import ChemicalGroupAnalyzer

from .constants import (
    ISSUE_CHEMICAL_INVALID,
    ISSUE_ER_OUT_OF_RANGE,
    ISSUE_GROUP1_MISSING,
    ISSUE_GROUP2_MISSING,
    ISSUE_PROPERTY_PREDICTION_FAILED,
    ISSUE_REACTION_INCOMPATIBLE,
    ISSUE_REQUESTED_GROUPS_FAILED,
    ISSUE_TG_OUT_OF_RANGE,
)
from .helpers import (
    build_design_suggestions,
    build_feedback_text,
    determine_optimization_mode,
    safe_float,
)
from .property_eval import check_tg_er_properties


def generate_feedback(
    monomer_1: str,
    monomer_2: str,
    group1: Optional[str],
    group2: Optional[str],
    target_tg: Optional[float],
    target_er: Optional[float],
    tol_tg: float = 10.0,
    tol_er: float = 5.0,
) -> Dict[str, Any]:
    chemical_validity_check = ChemicalValidityCheck()
    group_validity_check = GroupCheck()
    group_analyzer = ChemicalGroupAnalyzer()

    issue_codes: List[str] = []
    issues: List[str] = []
    property_result: Optional[Dict[str, Any]] = None

    is_valid = chemical_validity_check.check_chemical_validity(monomer_1, monomer_2)
    if not is_valid:
        issue_codes.append(ISSUE_CHEMICAL_INVALID)
        issues.append(
            "Chemical validity failed: one or both monomers are invalid SMILES or chemically implausible."
        )

        suggestions = build_design_suggestions(
            property_result=None,
            group1=group1,
            group2=group2,
            issue_codes=issue_codes,
        )
        feedback_text = build_feedback_text(issues, suggestions)

        return {
            "needs_revision": True,
            "is_valid": False,
            "issue_codes": issue_codes,
            "issues": issues,
            "suggestions": suggestions,
            "property_details": None,
            "optimization_mode": "joint",
            "priority_property": "none",
            "feedback_text": feedback_text,
        }

    has_reaction_consistency, group1_present, group2_present = group_analyzer.check_reaction_consistency(
        monomer_1, monomer_2
    )

    if not has_reaction_consistency:
        issue_codes.append(ISSUE_REACTION_INCOMPATIBLE)
        issues.append(
            "Crosslinking/reactivity compatibility failed: the monomer pair does not contain a compatible reactive combination for thermoset formation."
        )

    if group1 and group2:
        exact_group_ok = group_validity_check.check_exact_group_consistency(
            monomer_1, monomer_2, group1, group2
        )
        if not exact_group_ok:
            issue_codes.append(ISSUE_REQUESTED_GROUPS_FAILED)
            issues.append(
                f"Requested functional group constraint failed: group1 '{group1}' is not correctly satisfied in monomer1 and/or group2 '{group2}' is not correctly satisfied in monomer2."
            )

    if group1 and not group1_present:
        issue_codes.append(ISSUE_GROUP1_MISSING)
        issues.append(
            f"Required reactive group '{group1}' is missing or insufficient for crosslinking."
        )

    if group2 and not group2_present:
        issue_codes.append(ISSUE_GROUP2_MISSING)
        issues.append(
            f"Required reactive group '{group2}' is missing or insufficient for crosslinking."
        )

    if target_tg is not None and target_er is not None:
        property_result = check_tg_er_properties(
            monomer_1=monomer_1,
            monomer_2=monomer_2,
            target_tg=target_tg,
            target_er=target_er,
            tol_tg=tol_tg,
            tol_er=tol_er,
        )

        if property_result is None:
            issue_codes.append(ISSUE_PROPERTY_PREDICTION_FAILED)
            issues.append(
                "Property evaluation failed: unable to estimate Tg/Er for the proposed monomers."
            )
        else:
            dtg = safe_float(property_result.get("dtg"), 0.0) or 0.0
            der = safe_float(property_result.get("der"), 0.0) or 0.0
            pred_tg = safe_float(property_result.get("predicted_tg"))
            pred_er = safe_float(property_result.get("predicted_er"))
            ratio_1 = property_result.get("ratio_1", None)
            ratio_2 = property_result.get("ratio_2", None)

            property_result["tg_target"] = target_tg
            property_result["er_target"] = target_er

            if dtg > tol_tg:
                issue_codes.append(ISSUE_TG_OUT_OF_RANGE)
                if pred_tg is not None:
                    direction = "too low" if pred_tg < target_tg else "too high"
                    issues.append(
                        f"Tg alignment failed: predicted Tg is {direction}. "
                        f"Target Tg = {target_tg}, predicted Tg = {pred_tg}, absolute error = {dtg:.2f}."
                    )
                else:
                    issues.append(
                        f"Tg alignment failed: absolute Tg error = {dtg:.2f}, which exceeds tolerance {tol_tg:.2f}."
                    )

            if der > tol_er:
                issue_codes.append(ISSUE_ER_OUT_OF_RANGE)
                if pred_er is not None:
                    direction = "too low" if pred_er < target_er else "too high"
                    issues.append(
                        f"Er alignment failed: predicted Er is {direction}. "
                        f"Target Er = {target_er}, predicted Er = {pred_er}, absolute error = {der:.2f}."
                    )
                else:
                    issues.append(
                        f"Er alignment failed: absolute Er error = {der:.2f}, which exceeds tolerance {tol_er:.2f}."
                    )

            if ratio_1 is not None and ratio_2 is not None:
                issues.append(
                    f"Best evaluated composition ratio was monomer1:monomer2 = {ratio_1}:{ratio_2}."
                )

    optimization_mode, priority_property = determine_optimization_mode(property_result)

    suggestions = build_design_suggestions(
        property_result=property_result,
        group1=group1,
        group2=group2,
        issue_codes=issue_codes,
    )

    feedback_text = build_feedback_text(issues, suggestions)

    return {
        "needs_revision": len(issue_codes) > 0,
        "is_valid": len(issue_codes) == 0,
        "issue_codes": issue_codes,
        "issues": issues,
        "suggestions": suggestions,
        "property_details": property_result,
        "optimization_mode": optimization_mode,
        "priority_property": priority_property,
        "feedback_text": feedback_text,
    }
