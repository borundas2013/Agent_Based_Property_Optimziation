import sys
from pathlib import Path


def ensure_generator_on_syspath() -> None:
    """
    Preserve legacy behavior from `Agents/Router.py`:
    add `Agents/Generator` onto `sys.path` so imports like
    `from Generator...` continue to work.
    """
    base_dir = Path(__file__).resolve().parent.parent
    generator_dir = base_dir / "Generator"

    if str(generator_dir) not in sys.path:
        sys.path.insert(0, str(generator_dir))

