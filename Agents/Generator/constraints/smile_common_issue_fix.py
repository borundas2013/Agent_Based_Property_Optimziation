import re
from rdkit import Chem


_RING_PATTERN = re.compile(r"%(?P<long>\d{2})|(?P<short>\d)")


def _extract_ring_tokens(smiles: str):
    """
    Return SMILES ring tokens (e.g. '1', '2', '%10') in the order they appear.
    This is more faithful to SMILES than a plain '\\d+' regex and avoids
    leaving stray '%' characters behind.
    """
    tokens = []
    for match in _RING_PATTERN.finditer(smiles):
        if match.group("long") is not None:
            tokens.append(f"%{match.group('long')}")
        else:
            tokens.append(match.group("short"))
    return tokens


def _renumber_overused_ring_tokens(smiles: str) -> str:
    """
    For ring indices that appear more than twice (e.g. '1' used 4 times in
    'C1CC1C1C1C'), try to split them into additional, non-conflicting indices
    instead of just deleting them.

    Strategy (single-digit ring numbers only):
    - Keep the first two occurrences of each digit as-is.
    - For any additional occurrences:
      - Pair them up and assign new ring digits that are not already used
        in the SMILES (e.g. 2, 3, 4, ...).
      - If an odd extra occurrence remains without a partner, drop that one.
    """
    matches = list(_RING_PATTERN.finditer(smiles))

    # Track positions of single-digit ring tokens
    occurrences = {}
    for m in matches:
        if m.group("long") is not None:
            # Skip multi-digit '%nn' rings for now
            continue
        token = m.group("short")
        occurrences.setdefault(token, []).append(m.start())

    if not occurrences:
        return smiles

    chars = list(smiles)

    # Collect already-used single-digit ring indices
    used_digits = set(occurrences.keys())

    to_delete = set()

    for token, positions in occurrences.items():
        if len(positions) <= 2:
            continue  # nothing to renumber

        # Extra occurrences beyond the first valid pair
        extra_positions = positions[2:]

        # Digits we can use that are not already present or the same as current
        available_digits = [
            d for d in "123456789" if d not in used_digits and d != token
        ]
        avail_idx = 0

        # Assign new digits in pairs
        while len(extra_positions) >= 2 and avail_idx < len(available_digits):
            new_digit = available_digits[avail_idx]
            avail_idx += 1

            p1 = extra_positions.pop(0)
            p2 = extra_positions.pop(0)

            chars[p1] = new_digit
            chars[p2] = new_digit
            used_digits.add(new_digit)

        # Any leftover (unpaired) extra occurrence is dropped
        for p in extra_positions:
            to_delete.add(p)

    if not to_delete:
        return "".join(chars)

    return "".join(ch for idx, ch in enumerate(chars) if idx not in to_delete)


def _drop_overused_ring_tokens(smiles: str) -> str:
    """
    Last-resort cleanup: if RDKit still cannot parse after gentler fixes,
    drop all remaining ring closure tokens entirely and linearize the
    structure. This sacrifices ring information but recovers a parseable
    molecule in many corrupt cases.
    """
    ring_tokens = set(_extract_ring_tokens(smiles))
    if not ring_tokens:
        return smiles

    result = smiles
    for token in ring_tokens:
        result = re.sub(re.escape(token), "", result)
    return result


def fix_smiles_parsing_issues(smiles):
    """
    Fix common SMILES parsing issues including invalid characters, unmatched parentheses, 
    and malformed ring structures.
    
    Args:
        smiles (str): Input SMILES string that may have parsing issues

    Returns:
        str: Fixed SMILES string, or original if no fixes possible
    """
    
    if not smiles or smiles in ['nan', 'Not found', 'N/A', '']:
        return smiles
    
    original_smiles = smiles
    fixed_smiles = smiles
    
    try:
        # 1. Remove clearly invalid characters that are not part of SMILES syntax
        # Keep SMILES-relevant symbols like '+', '%', digits, and element letters.
        invalid_chars = ['?', '!', '^', '&', '*', '|', '<', '>', '~']
        for char in invalid_chars:
            fixed_smiles = fixed_smiles.replace(char, '')
        
        # 2. Fix empty parentheses - remove them completely
        fixed_smiles = re.sub(r'\(\)', '', fixed_smiles)
        
        # 3. Fix consecutive parentheses
        fixed_smiles = re.sub(r'\(+', '(', fixed_smiles)
        fixed_smiles = re.sub(r'\)+', ')', fixed_smiles)
        
        # 4. Fix unmatched parentheses
        open_parens = fixed_smiles.count('(')
        close_parens = fixed_smiles.count(')')

        if open_parens > close_parens:
            extra_open = open_parens - close_parens
            # Prefer removing dangling '(' at the end (common corruption)
            for _ in range(extra_open):
                if fixed_smiles.endswith('('):
                    fixed_smiles = fixed_smiles[:-1]
                else:
                    # Otherwise close the remaining open parentheses
                    fixed_smiles += ')'
        elif close_parens > open_parens:
            # Remove extra close parentheses from the end
            extra_close = close_parens - open_parens
            for _ in range(extra_close):
                if fixed_smiles.endswith(')'):
                    fixed_smiles = fixed_smiles[:-1]

        # Remove any empty parentheses that may have been created while balancing
        fixed_smiles = re.sub(r'\(\)', '', fixed_smiles)

        # If the whole string is a single outer branch like "(CC1CCCCC)",
        # unwrap it to "CC1CCCCC" so that it can be further fixed.
        m_outer = re.match(r'^\(([^()]*)\)$', fixed_smiles)
        if m_outer:
            fixed_smiles = m_outer.group(1)

        # Remove leading orphan branch groups like "(C)CCCC" which RDKit
        # cannot parse because a SMILES cannot start with a branch.
        # We conservatively drop those leading branches as a heuristic.
        while fixed_smiles.startswith('('):
            m = re.match(r'^\([^)]*\)', fixed_smiles)
            if not m:
                break
            fixed_smiles = fixed_smiles[m.end():]
        
        # 3. Fix ring closure issues (dangling / overused rings)
        ring_tokens = _extract_ring_tokens(fixed_smiles)
        ring_counts = {}
        for token in ring_tokens:
            ring_counts[token] = ring_counts.get(token, 0) + 1

        # Remove dangling ring tokens (appear only once)
        for token, count in ring_counts.items():
            if count == 1:
                fixed_smiles = re.sub(re.escape(token), '', fixed_smiles, count=1)

        # Renumber overused ring indices like C1CC1C1C1C -> C1CC1C2C2C
        fixed_smiles = _renumber_overused_ring_tokens(fixed_smiles)
        
        # 4. Fix common SMILES syntax issues
        # Remove consecutive dots (should be single dot)
        fixed_smiles = re.sub(r'\.+', '.', fixed_smiles)
        
        # Fix common atom notation issues
        fixed_smiles = re.sub(r'([A-Z])([A-Z])', r'\1\2', fixed_smiles)  # Ensure proper atom notation
        
        # 5. Try RDKit validation and canonicalization
        try:
            mol = Chem.MolFromSmiles(fixed_smiles)
            if mol is not None:
                canonical_smiles = Chem.MolToSmiles(mol)
                if canonical_smiles and canonical_smiles != fixed_smiles:
                    fixed_smiles = canonical_smiles
        except:
            pass
        
        # 6. Final validation - if still invalid, try more aggressive fixes
        try:
            mol = Chem.MolFromSmiles(fixed_smiles)
            if mol is None:
                # First, drop clearly overused ring indices entirely
                fixed_smiles = _drop_overused_ring_tokens(fixed_smiles)
                mol = Chem.MolFromSmiles(fixed_smiles)

                if mol is None:
                    # Then try removing remaining invalid characters
                    fixed_smiles = re.sub(r'[^A-Za-z0-9()=#@+-\[\]\.]', '', fixed_smiles)
                    
                    # Try again
                    mol = Chem.MolFromSmiles(fixed_smiles)
                    if mol is not None:
                        fixed_smiles = Chem.MolToSmiles(mol)
        except:
            pass
        
        # If all fixes fail, return original
        if fixed_smiles == original_smiles or not fixed_smiles:
            return original_smiles
            
        return fixed_smiles
        
    except Exception as e:
        # If any error occurs during fixing, return original
        return original_smiles


def detect_and_fix_dangling_rings(smiles):
    # Find all ring closure tokens (e.g. '1', '2', '%10')
    ring_tokens = _extract_ring_tokens(smiles)

    # Count occurrences of each ring token
    ring_counts = {}
    for token in ring_tokens:
        ring_counts[token] = ring_counts.get(token, 0) + 1
    
    # Find issues
    issues = []
    for token, count in ring_counts.items():
        if count == 1:
            issues.append(f"Ring {token} appears only once (dangling)")
        elif count > 2:
            issues.append(f"Ring {token} appears {count} times (invalid)")

    # Fix dangling rings by removing the ring closure tokens
    fixed_smiles = smiles
    for token, count in ring_counts.items():
        if count == 1:
            # Remove the specific dangling ring token
            fixed_smiles = re.sub(re.escape(token), '', fixed_smiles, count=1)
            issues.append(f"Removed dangling ring {token}")

    # Renumber overused ring indices as a first attempt
    fixed_smiles = _renumber_overused_ring_tokens(fixed_smiles)
    
    # Try RDKit canonicalization
    try:
        mol = Chem.MolFromSmiles(fixed_smiles)
        if mol is None:
            # If RDKit still cannot parse, drop overused ring indices
            fixed_smiles = _drop_overused_ring_tokens(fixed_smiles)
            mol = Chem.MolFromSmiles(fixed_smiles)

        if mol is not None:
            rdkit_fixed = Chem.MolToSmiles(mol)
            if rdkit_fixed != fixed_smiles:
                fixed_smiles = rdkit_fixed
                issues.append("RDKit canonicalization applied")
        else:
            issues.append("RDKit could not process fixed SMILES even after dropping overused rings")
    except:
        issues.append("RDKit processing failed")
    
    return fixed_smiles


if __name__ == "__main__":
    # Complex test cases for manual checking
    test_smiles = [
        # 1. Simple dangling single‑digit ring
        "(C)C(CC1CCCCC)",
        "C1CCCCC2C1CCC",
       
    ]

    for s in test_smiles:
        fixed_general = fix_smiles_parsing_issues(s)
        fixed_rings = detect_and_fix_dangling_rings(fixed_general)

        try:
            mol_orig = Chem.MolFromSmiles(s)
        except Exception:
            mol_orig = None
        try:
            mol_gen = Chem.MolFromSmiles(fixed_general)
        except Exception:
            mol_gen = None
        try:
            mol_ring = Chem.MolFromSmiles(fixed_rings)
        except Exception:
            mol_ring = None

        print("===")
        print("Original:", s)
        print("  Parsed:", mol_orig is not None)
        print("Fixed (general):", fixed_general)
        print("  Parsed:", mol_gen is not None)
        print("Fixed (rings):", fixed_rings)
        print("  Parsed:", mol_ring is not None)