"""Ensure Agents/, Generator/, and this package dir are on sys.path for sibling imports."""
from __future__ import annotations

import os
import sys

_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_AGENTS_ROOT = os.path.dirname(_AGENT_DIR)
_GENERATOR_ROOT = os.path.join(_AGENTS_ROOT, "Generator")

# Agents + Generator are needed for `feedback`, `Generator.constraints`, etc.
for _p in (_AGENTS_ROOT, _GENERATOR_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# This package must be *first*: `Agents/Generator` also ships `template.py`, which would
# shadow `GeneratorAgent/template.py` if Generator appears earlier on sys.path.
if _AGENT_DIR in sys.path:
    try:
        sys.path.remove(_AGENT_DIR)
    except ValueError:
        pass
sys.path.insert(0, _AGENT_DIR)
