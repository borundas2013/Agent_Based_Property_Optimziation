from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Tuple, Optional
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors


# ============================================================
# Data classes
# ============================================================

@dataclass
class RuleSuggestion:
    rule_name: str
    direction: str              # "increase" or "decrease"
    action: str
    rationale: str
    applicability_score: float
    repeat_times: int


@dataclass
class TgDecisionResult:
    monomer_1: str
    monomer_2: str
    predicted_tg: float
    target_tg: float
    tg_gap: float
    direction: str              # "increase", "decrease", or "keep"
    features: Dict[str, Any]
    suggestions: List[RuleSuggestion]


# ============================================================
# SMARTS patterns
# These are heuristic patterns, not exhaustive chemistry.
# ============================================================

SMARTS = {
    # Aromatic / rigid
    "aromatic_ring": Chem.MolFromSmarts("a1aaaaa1"),
    "cyclohexane_like": Chem.MolFromSmarts("[R]"),   # any ring atom, broad heuristic
    "fused_ring": Chem.MolFromSmarts("[R2]"),        # atom in 2 rings, rough fused-ring proxy

    # Flexible linkers / spacers
    "ether": Chem.MolFromSmarts("[OD2]([#6])[#6]"),
    "long_aliphatic_3": Chem.MolFromSmarts("[CH2][CH2][CH2]"),
    "long_aliphatic_4": Chem.MolFromSmarts("[CH2][CH2][CH2][CH2]"),

    # Polar rigid groups
    "amide": Chem.MolFromSmarts("C(=O)N"),
    "imide": Chem.MolFromSmarts("N(C(=O))C=O"),
    "urethane": Chem.MolFromSmarts("NC(=O)O"),
    "urea": Chem.MolFromSmarts("NC(=O)N"),
    "ester": Chem.MolFromSmarts("C(=O)O"),
    "hydroxyl": Chem.MolFromSmarts("[OX2H]"),
    "nitrile": Chem.MolFromSmarts("C#N"),
    "sulfone": Chem.MolFromSmarts("S(=O)(=O)"),

    # Reactive / crosslink-related groups
    "epoxy": Chem.MolFromSmarts("C1OC1"),
    "amine_primary_secondary": Chem.MolFromSmarts("[NX3;H2,H1;!$(NC=O)]"),
    "hydroxyl_reactive": Chem.MolFromSmarts("[OX2H]"),
    "isocyanate": Chem.MolFromSmarts("N=C=O"),
    "carboxylic_acid": Chem.MolFromSmarts("C(=O)[OH]"),
    "anhydride": Chem.MolFromSmarts("C(=O)OC(=O)"),
    "vinyl": Chem.MolFromSmarts("C=C"),
}


# ============================================================
# Helper functions
# ============================================================

def mol_from_smiles(smiles: str) -> Optional[Chem.Mol]:
    mol = Chem.MolFromSmiles(smiles)
    return mol


def count_matches(mol: Chem.Mol, pattern: Chem.Mol) -> int:
    if mol is None or pattern is None:
        return 0
    matches = mol.GetSubstructMatches(pattern)
    return len(matches)


def safe_ring_info(mol: Chem.Mol) -> Tuple[int, int]:
    """
    Returns:
        total ring count,
        aromatic ring count
    """
    ring_count = rdMolDescriptors.CalcNumRings(mol)
    aromatic_ring_count = rdMolDescriptors.CalcNumAromaticRings(mol)
    return ring_count, aromatic_ring_count


def estimate_longest_aliphatic_spacer(mol: Chem.Mol) -> int:
    """
    Rough heuristic:
    Count longest path of connected non-ring sp3 carbon atoms.
    This is not exact, but useful for direction rules.
    """
    if mol is None:
        return 0

    carbon_indices = []
    for atom in mol.GetAtoms():
        if (
            atom.GetAtomicNum() == 6
            and not atom.GetIsAromatic()
            and not atom.IsInRing()
            and atom.GetHybridization().name == "SP3"
        ):
            carbon_indices.append(atom.GetIdx())

    carbon_set = set(carbon_indices)
    if not carbon_set:
        return 0

    adjacency = {idx: [] for idx in carbon_indices}
    for bond in mol.GetBonds():
        a1 = bond.GetBeginAtomIdx()
        a2 = bond.GetEndAtomIdx()
        if a1 in carbon_set and a2 in carbon_set:
            adjacency[a1].append(a2)
            adjacency[a2].append(a1)

    visited = set()
    max_component_size = 0

    for start in carbon_indices:
        if start in visited:
            continue
        stack = [start]
        component = []
        visited.add(start)

        while stack:
            node = stack.pop()
            component.append(node)
            for nbr in adjacency[node]:
                if nbr not in visited:
                    visited.add(nbr)
                    stack.append(nbr)

        max_component_size = max(max_component_size, len(component))

    return max_component_size


def count_reactive_groups(mol: Chem.Mol) -> int:
    reactive_keys = [
        "epoxy",
        "amine_primary_secondary",
        "hydroxyl_reactive",
        "isocyanate",
        "carboxylic_acid",
        "anhydride",
        "vinyl",
    ]
    total = 0
    for key in reactive_keys:
        total += count_matches(mol, SMARTS[key])
    return total


def count_polar_rigid_groups(mol: Chem.Mol) -> int:
    keys = ["amide", "imide", "urethane", "urea", "ester", "nitrile", "sulfone"]
    total = 0
    for key in keys:
        total += count_matches(mol, SMARTS[key])
    return total


def count_flexible_linkers(mol: Chem.Mol) -> int:
    ether_count = count_matches(mol, SMARTS["ether"])
    return ether_count


def count_rigid_cycles(mol: Chem.Mol) -> int:
    total_rings, aromatic_rings = safe_ring_info(mol)
    fused_atoms = count_matches(mol, SMARTS["fused_ring"])
    # simple heuristic: aromatic rings + non-aromatic rings + fused bonus
    return total_rings + fused_atoms + aromatic_rings


def analyze_monomer(mol: Chem.Mol) -> Dict[str, Any]:
    total_rings, aromatic_rings = safe_ring_info(mol)

    return {
        "total_rings": total_rings,
        "aromatic_rings": aromatic_rings,
        "rigid_cycles": count_rigid_cycles(mol),
        "reactive_group_count": count_reactive_groups(mol),
        "polar_rigid_group_count": count_polar_rigid_groups(mol),
        "flexible_linker_count": count_flexible_linkers(mol),
        "longest_aliphatic_spacer": estimate_longest_aliphatic_spacer(mol),
        "mol_weight": rdMolDescriptors.CalcExactMolWt(mol),
        "hbond_donors": rdMolDescriptors.CalcNumHBD(mol),
        "hbond_acceptors": rdMolDescriptors.CalcNumHBA(mol),
    }


def combine_features(f1: Dict[str, Any], f2: Dict[str, Any]) -> Dict[str, Any]:
    combined = {}
    for key in f1.keys():
        combined[key] = f1[key] + f2[key]

    # extra normalized / interpreted flags
    combined["average_aliphatic_spacer"] = (
        f1["longest_aliphatic_spacer"] + f2["longest_aliphatic_spacer"]
    ) / 2.0

    combined["estimated_crosslink_potential"] = combined["reactive_group_count"]

    return combined


# ============================================================
# Repeat policy
# ============================================================

def decide_repeat_times(tg_gap_abs: float, rule_strength: str = "medium") -> int:
    """
    Heuristic repeat policy.
    """
    if tg_gap_abs < 10:
        base = 1
    elif tg_gap_abs < 30:
        base = 2
    else:
        base = 3

    if rule_strength == "strong":
        return min(base, 2)
    elif rule_strength == "weak":
        return min(base + 1, 3)
    return min(base, 3)


# ============================================================
# Rule scoring
# Larger score => more applicable
# ============================================================

def score_increase_rules(features: Dict[str, Any], tg_gap_abs: float) -> List[RuleSuggestion]:
    suggestions = []

    aromatic = features["aromatic_rings"]
    rigid = features["rigid_cycles"]
    reactive = features["reactive_group_count"]
    spacer = features["average_aliphatic_spacer"]
    polar = features["polar_rigid_group_count"]
    flexible = features["flexible_linker_count"]

    # 1. Add aromatic ring
    score = max(0.0, 3.0 - aromatic) + 0.03 * tg_gap_abs
    suggestions.append(
        RuleSuggestion(
            rule_name="add_aromatic_ring",
            direction="increase",
            action="Add aromatic ring / phenyl-containing motif",
            rationale="Low aromatic content suggests room to increase backbone rigidity.",
            applicability_score=score,
            repeat_times=decide_repeat_times(tg_gap_abs, "medium"),
        )
    )

    # 2. Add rigid cyclic group
    score = max(0.0, 3.0 - rigid) + 0.025 * tg_gap_abs
    suggestions.append(
        RuleSuggestion(
            rule_name="add_rigid_cyclic_group",
            direction="increase",
            action="Add rigid cyclic motif such as cycloaliphatic or fused rigid ring unit",
            rationale="Low ring rigidity suggests Tg may be improved by restricting rotation.",
            applicability_score=score,
            repeat_times=decide_repeat_times(tg_gap_abs, "medium"),
        )
    )

    # 3. Increase functionality / crosslink density
    score = max(0.0, 4.0 - reactive) + 0.04 * tg_gap_abs
    suggestions.append(
        RuleSuggestion(
            rule_name="increase_crosslink_density",
            direction="increase",
            action="Increase reactive functionality to promote higher crosslink density",
            rationale="Low reactive-group count suggests lower network constraint.",
            applicability_score=score,
            repeat_times=decide_repeat_times(tg_gap_abs, "strong"),
        )
    )

    # 4. Shorten aliphatic spacer
    score = max(0.0, spacer - 2.0) + 0.03 * tg_gap_abs
    suggestions.append(
        RuleSuggestion(
            rule_name="shorten_aliphatic_spacer",
            direction="increase",
            action="Shorten long aliphatic spacer segments",
            rationale="Long flexible aliphatic spacers usually increase chain mobility and reduce Tg.",
            applicability_score=score,
            repeat_times=decide_repeat_times(tg_gap_abs, "strong"),
        )
    )

    # 5. Add strong polar rigid group
    score = max(0.0, 2.0 - polar) + 0.02 * tg_gap_abs
    suggestions.append(
        RuleSuggestion(
            rule_name="add_polar_rigid_group",
            direction="increase",
            action="Add rigid polar group such as amide, imide, urethane, urea, sulfone, or nitrile-bearing rigid unit",
            rationale="Low polar-rigid-group content suggests limited intermolecular restriction.",
            applicability_score=score,
            repeat_times=decide_repeat_times(tg_gap_abs, "medium"),
        )
    )

    # 6. Replace flexible linker with rigid linker
    score = flexible + 0.03 * tg_gap_abs
    suggestions.append(
        RuleSuggestion(
            rule_name="replace_flexible_linker_with_rigid",
            direction="increase",
            action="Replace flexible linker (for example ether/aliphatic spacer) with a rigid linker",
            rationale="Flexible linkers are present and likely contribute to lower Tg.",
            applicability_score=score,
            repeat_times=decide_repeat_times(tg_gap_abs, "strong"),
        )
    )

    suggestions.sort(key=lambda x: x.applicability_score, reverse=True)
    return suggestions


def score_decrease_rules(features: Dict[str, Any], tg_gap_abs: float) -> List[RuleSuggestion]:
    suggestions = []

    aromatic = features["aromatic_rings"]
    rigid = features["rigid_cycles"]
    reactive = features["reactive_group_count"]
    spacer = features["average_aliphatic_spacer"]
    polar = features["polar_rigid_group_count"]
    flexible = features["flexible_linker_count"]

    # 1. Add long aliphatic spacer
    score = max(0.0, 4.0 - spacer) + 0.03 * tg_gap_abs
    suggestions.append(
        RuleSuggestion(
            rule_name="add_long_aliphatic_spacer",
            direction="decrease",
            action="Add or extend long aliphatic spacer",
            rationale="Short or limited aliphatic flexibility suggests Tg can be reduced by adding soft spacer segments.",
            applicability_score=score,
            repeat_times=decide_repeat_times(tg_gap_abs, "medium"),
        )
    )

    # 2. Add flexible ether linker
    score = max(0.0, 2.0 - flexible) + 0.03 * tg_gap_abs
    suggestions.append(
        RuleSuggestion(
            rule_name="add_flexible_ether_linker",
            direction="decrease",
            action="Insert or increase flexible ether linker content",
            rationale="Ether linkers typically increase rotational freedom and reduce Tg.",
            applicability_score=score,
            repeat_times=decide_repeat_times(tg_gap_abs, "medium"),
        )
    )

    # 3. Reduce aromatic content
    score = aromatic + 0.02 * tg_gap_abs
    suggestions.append(
        RuleSuggestion(
            rule_name="reduce_aromatic_content",
            direction="decrease",
            action="Reduce aromatic content or replace aromatic unit with flexible aliphatic unit",
            rationale="Aromatic rings contribute to rigidity and elevated Tg.",
            applicability_score=score,
            repeat_times=decide_repeat_times(tg_gap_abs, "strong"),
        )
    )

    # 4. Reduce functionality / crosslink density
    score = reactive + 0.04 * tg_gap_abs
    suggestions.append(
        RuleSuggestion(
            rule_name="reduce_crosslink_density",
            direction="decrease",
            action="Reduce reactive functionality / crosslink density",
            rationale="High crosslink potential often increases network constraint and Tg.",
            applicability_score=score,
            repeat_times=decide_repeat_times(tg_gap_abs, "strong"),
        )
    )

    # 5. Increase distance between reactive groups
    score = max(0.0, 4.0 - spacer) + max(0.0, reactive - 1.0) + 0.03 * tg_gap_abs
    suggestions.append(
        RuleSuggestion(
            rule_name="increase_reactive_group_spacing",
            direction="decrease",
            action="Increase distance between reactive groups using spacer insertion",
            rationale="Longer segment length between crosslinks usually lowers Tg.",
            applicability_score=score,
            repeat_times=decide_repeat_times(tg_gap_abs, "medium"),
        )
    )

    # 6. Replace rigid linker with flexible linker
    score = rigid + aromatic + 0.03 * tg_gap_abs
    suggestions.append(
        RuleSuggestion(
            rule_name="replace_rigid_linker_with_flexible",
            direction="decrease",
            action="Replace rigid linker with flexible linker such as ether or aliphatic chain",
            rationale="High rigid/aromatic content suggests Tg can be reduced by increasing flexibility.",
            applicability_score=score,
            repeat_times=decide_repeat_times(tg_gap_abs, "strong"),
        )
    )

    suggestions.sort(key=lambda x: x.applicability_score, reverse=True)
    return suggestions


# ============================================================
# Main decision engine
# ============================================================

def decide_tg_rules(
    monomer_1: str,
    monomer_2: str,
    predicted_tg: float,
    target_tg: float,
    threshold: float = 5.0,
    top_k: int = 4,
) -> TgDecisionResult:
    """
    Main rule-based decision function.
    """

    mol1 = mol_from_smiles(monomer_1)
    mol2 = mol_from_smiles(monomer_2)

    if mol1 is None:
        raise ValueError(f"Invalid SMILES for monomer_1: {monomer_1}")
    if mol2 is None:
        raise ValueError(f"Invalid SMILES for monomer_2: {monomer_2}")

    f1 = analyze_monomer(mol1)
    f2 = analyze_monomer(mol2)
    features = combine_features(f1, f2)

    tg_gap = target_tg - predicted_tg

    if tg_gap > threshold:
        direction = "increase"
        suggestions = score_increase_rules(features, abs(tg_gap))[:top_k]

    elif tg_gap < -threshold:
        direction = "decrease"
        suggestions = score_decrease_rules(features, abs(tg_gap))[:top_k]

    else:
        direction = "keep"
        suggestions = []

    return TgDecisionResult(
        monomer_1=monomer_1,
        monomer_2=monomer_2,
        predicted_tg=predicted_tg,
        target_tg=target_tg,
        tg_gap=tg_gap,
        direction=direction,
        features=features,
        suggestions=suggestions,
    )


# ============================================================
# Optional utility: pretty print
# ============================================================

def print_tg_decision(result: TgDecisionResult) -> None:
    print("=" * 80)
    print("Tg RULE DECISION RESULT")
    print("=" * 80)
    print(f"Monomer 1   : {result.monomer_1}")
    print(f"Monomer 2   : {result.monomer_2}")
    print(f"Predicted Tg: {result.predicted_tg}")
    print(f"Target Tg   : {result.target_tg}")
    print(f"Tg gap      : {result.tg_gap:.2f}")
    print(f"Direction   : {result.direction}")
    print("\nFeatures:")
    for k, v in result.features.items():
        print(f"  - {k}: {v}")

    print("\nSuggestions:")
    if not result.suggestions:
        print("  No rule-based modification suggested. Candidate is close enough to target.")
    else:
        for i, s in enumerate(result.suggestions, 1):
            print(f"\n  {i}. {s.rule_name}")
            print(f"     action       : {s.action}")
            print(f"     rationale    : {s.rationale}")
            print(f"     score        : {s.applicability_score:.3f}")
            print(f"     repeat_times : {s.repeat_times}")


# ============================================================
# Example usage
# ============================================================

# if __name__ == "__main__":
#     # Example monomers only for demonstration
#     monomer_1 = "OCC(O)CO"                  # glycerol-like
#     monomer_2 = "c1cc(ccc1O)C(C)(C)C"       # aromatic alcohol-like motif

#     predicted_tg = 95.0
#     target_tg = 145.0

#     result = decide_tg_rules(
#         monomer_1=monomer_1,
#         monomer_2=monomer_2,
#         predicted_tg=predicted_tg,
#         target_tg=target_tg,
#         threshold=5.0,
#         top_k=4,
#     )

#     print_tg_decision(result)