"""
Refinement / repair helpers for TSMP design.

This package holds the logic that was previously in
`LLM_Reviser/repair_mechanism.py`, split into smaller modules.
"""

from .validation import (
    safe_parse_llm_output,
    validate_smiles,
    has_reaction_constraints,
    compute_similarity,
    validate_revised_candidate,
)
from .unified_request import (
    REPAIR_SYSTEM_PROMPT,
    build_unified_revision_request,
    make_unified_revision_messages,
)

__all__ = [
    "safe_parse_llm_output",
    "validate_smiles",
    "has_reaction_constraints",
    "compute_similarity",
    "validate_revised_candidate",
    "REPAIR_SYSTEM_PROMPT",
    "build_unified_revision_request",
    "make_unified_revision_messages",
]

