import re
from typing import Optional, Tuple


def _extract_smiles_from_text(text: str) -> Optional[str]:
    """
    Extract SMILES string from text. SMILES typically:
    - Contains alphanumeric characters, =, (, ), [, ], @, /, \, +, -, #
    - Usually doesn't contain spaces (except in rare cases)
    - Often appears after a colon or on its own line
    """
    if not text:
        return None
    
    text = text.strip()
    
    # Remove common trailing punctuation (but keep SMILES-relevant chars like ')' and ']')
    text = text.rstrip(".,;:!?")
    
    # Remove quotes if present
    text = text.strip('`"\'').strip()
    
    # SMILES pattern: alphanumeric + common SMILES characters
    # SMILES can contain: letters, numbers, =, (, ), [, ], @, /, \, +, -, #, %, ., *
    smiles_pattern = r'[A-Za-z0-9=()\[\]@/\\+\-#%.*]+'
    
    # Try to find SMILES-like string
    # First, try to find after colon (common pattern)
    if ':' in text:
        after_colon = text.split(':', 1)[1].strip()
        match = re.search(smiles_pattern, after_colon)
        if match:
            smiles = match.group(0)
            # Clean up: remove trailing punctuation (but keep SMILES chars)
            smiles = smiles.rstrip(".,;:!?")
            return smiles if smiles else None
    
    # If no colon, try to extract SMILES directly
    match = re.search(smiles_pattern, text)
    if match:
        smiles = match.group(0)
        # Clean up: remove trailing punctuation (but keep SMILES chars)
        smiles = smiles.rstrip(".,;:!?")
        return smiles if smiles else None
    
    return None

def extract_monomer_smiles(completion: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Robust extraction for various formats:
      - Monomer 1: SMILES
      - Monomer 1 (desc): SMILES
      - C1OC1 in Monomer 1: SMILES
      - Monomer 1 (desc) SMILES   (no colon)
      - Monomer 2: SMILES
      etc.
    """
    # Pattern 1: Handle "X in Monomer 1: SMILES" or "Monomer 1: SMILES"
    # Matches: "- C1OC1 in Monomer 1: SMILES" or "Monomer 1: SMILES" or "Monomer 1 (desc): SMILES"
    pat1 = re.compile(
        r"(?:[^\n]*?\s+in\s+)?monomer\s*1\s*(?:\([^)]*\))?\s*:?\s*(.*?)(?=\n\s*(?:[^\n]*?\s+in\s+)?monomer\s*2\b|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    
    # Pattern 2: Handle "X in Monomer 2: SMILES" or "Monomer 2: SMILES"
    pat2 = re.compile(
        r"(?:[^\n]*?\s+in\s+)?monomer\s*2\s*(?:\([^)]*\))?\s*:?\s*(.*?)(?=\n\s*(?:[^\n]*?\s+in\s+)?monomer\s*1\b|\Z)",
        re.IGNORECASE | re.DOTALL,
    )

    m1 = pat1.search(completion)
    m2 = pat2.search(completion)

    chunk1 = m1.group(1).strip() if m1 else ""
    chunk2 = m2.group(1).strip() if m2 else ""

    # Extract SMILES from each chunk
    # Take first line if multiple lines, then extract SMILES
    cand1 = chunk1.splitlines()[0].strip() if chunk1 else ""
    cand2 = chunk2.splitlines()[0].strip() if chunk2 else ""

    monomer1 = _extract_smiles_from_text(cand1)
    monomer2 = _extract_smiles_from_text(cand2)

    print("Monomer 1:", monomer1, " Monomer2: ", monomer2)
    return monomer1, monomer2




