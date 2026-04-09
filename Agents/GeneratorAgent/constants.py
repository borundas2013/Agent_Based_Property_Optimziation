from __future__ import annotations

import paths  # noqa: F401

from feedback.feedback import (
    ISSUE_CHEMICAL_INVALID,
    ISSUE_GROUP1_MISSING,
    ISSUE_GROUP2_MISSING,
    ISSUE_REACTION_INCOMPATIBLE,
    ISSUE_REQUESTED_GROUPS_FAILED,
)

# Ranking: validity, reaction compatibility, and group consistency first; then lower Tg/Er error.
STRUCTURAL_ISSUE_CODES = frozenset(
    {
        ISSUE_CHEMICAL_INVALID,
        ISSUE_REACTION_INCOMPATIBLE,
        ISSUE_REQUESTED_GROUPS_FAILED,
        ISSUE_GROUP1_MISSING,
        ISSUE_GROUP2_MISSING,
    }
)
