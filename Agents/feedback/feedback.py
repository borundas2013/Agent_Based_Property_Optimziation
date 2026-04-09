from __future__ import annotations

# Public entrypoint module kept for backward compatibility.
# Existing imports like `from feedback.feedback import generate_feedback` will keep working.
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
from .generator import generate_feedback
from .helpers import build_design_suggestions, build_feedback_text, determine_optimization_mode, safe_float
from .property_eval import check_property, check_tg_er_properties

__all__ = [
    "ISSUE_CHEMICAL_INVALID",
    "ISSUE_REACTION_INCOMPATIBLE",
    "ISSUE_REQUESTED_GROUPS_FAILED",
    "ISSUE_GROUP1_MISSING",
    "ISSUE_GROUP2_MISSING",
    "ISSUE_PROPERTY_PREDICTION_FAILED",
    "ISSUE_TG_OUT_OF_RANGE",
    "ISSUE_ER_OUT_OF_RANGE",
    "safe_float",
    "determine_optimization_mode",
    "build_design_suggestions",
    "build_feedback_text",
    "check_property",
    "check_tg_er_properties",
    "generate_feedback",
]