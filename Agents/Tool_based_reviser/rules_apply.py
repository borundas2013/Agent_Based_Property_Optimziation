from dataclasses import dataclass
from typing import Optional
from rdkit import Chem

from Tool_based_reviser.decision_rules import mol_from_smiles, analyze_monomer, decide_tg_rules, print_tg_decision
#from Generator.ConstraintsChecking import check_tg_er_properties

IMPLEMENTED_RULES = {
    "add_aromatic_ring",
    "add_flexible_ether_linker",
    "add_long_aliphatic_spacer",
    "add_polar_rigid_group",
}

@dataclass
class ModificationResult:
    applied_rule: str
    original_smiles: str
    modified_smiles: Optional[str]
    modified_mol: Optional[Chem.Mol]
    success: bool
    message: str


@dataclass
class TgRefinementResult:
    original_monomer_1: str
    original_monomer_2: str
    modified_monomer_1: str
    modified_monomer_2: str
    applied_rule: str
    original_predicted_tg: float
    #new_predicted_tg: float
    #tg_improvement: float
    #target_tg: float
    #reached_target: bool

def apply_best_available_rule(
    monomer_1: str,
    monomer_2: str,
    suggestions
):
    for suggestion in suggestions:
        rule_name = suggestion.rule_name

        if rule_name not in IMPLEMENTED_RULES:
            continue

        monomer_index = choose_monomer_to_modify(monomer_1, monomer_2, rule_name)

        if monomer_index == 1:
            mod_result = apply_rule_to_smiles(monomer_1, rule_name)
            if mod_result.success and mod_result.modified_smiles:
                return {
                    "rule_name": rule_name,
                    "new_m1": mod_result.modified_smiles,
                    "new_m2": monomer_2,
                    "mod_result": mod_result,
                }
        else:
            mod_result = apply_rule_to_smiles(monomer_2, rule_name)
            if mod_result.success and mod_result.modified_smiles:
                return {
                    "rule_name": rule_name,
                    "new_m1": monomer_1,
                    "new_m2": mod_result.modified_smiles,
                    "mod_result": mod_result,
                }

    return None
def mol_to_smiles_safe(mol: Optional[Chem.Mol]) -> Optional[str]:
    if mol is None:
        return None
    try:
        Chem.SanitizeMol(mol)
        return Chem.MolToSmiles(mol, canonical=True)
    except Exception:
        return None


def validate_mol(mol: Optional[Chem.Mol]) -> bool:
    if mol is None:
        return False
    try:
        Chem.SanitizeMol(mol)
        return True
    except Exception:
        return False

def choose_monomer_to_modify(monomer_1: str, monomer_2: str, rule_name: str) -> int:
    """
    Returns 1 or 2 depending on which monomer is the better candidate for modification.
    """
    mol1 = mol_from_smiles(monomer_1)
    mol2 = mol_from_smiles(monomer_2)

    if mol1 is None or mol2 is None:
        return 1

    f1 = analyze_monomer(mol1)
    f2 = analyze_monomer(mol2)

    if rule_name in {"add_aromatic_ring", "add_rigid_cyclic_group", "add_polar_rigid_group"}:
        return 1 if f1["aromatic_rings"] <= f2["aromatic_rings"] else 2

    if rule_name in {"shorten_aliphatic_spacer", "replace_flexible_linker_with_rigid"}:
        return 1 if f1["longest_aliphatic_spacer"] >= f2["longest_aliphatic_spacer"] else 2

    if rule_name in {"increase_crosslink_density"}:
        return 1 if f1["reactive_group_count"] <= f2["reactive_group_count"] else 2

    if rule_name in {"add_long_aliphatic_spacer", "add_flexible_ether_linker"}:
        return 1 if f1["longest_aliphatic_spacer"] <= f2["longest_aliphatic_spacer"] else 2

    if rule_name in {"reduce_aromatic_content", "replace_rigid_linker_with_flexible"}:
        return 1 if f1["aromatic_rings"] >= f2["aromatic_rings"] else 2

    return 1
def modify_add_aromatic_ring(smiles: str) -> ModificationResult:
    try:
        mol = mol_from_smiles(smiles)
        if mol is None:
            return ModificationResult(
                applied_rule="add_aromatic_ring",
                original_smiles=smiles,
                modified_smiles=None,
                modified_mol=None,
                success=False,
                message="Invalid original SMILES."
            )

        phenyl = Chem.MolFromSmiles("c1ccccc1")
        combined = Chem.CombineMols(mol, phenyl)
        modified_smiles = mol_to_smiles_safe(combined)

        if modified_smiles is None:
            return ModificationResult(
                applied_rule="add_aromatic_ring",
                original_smiles=smiles,
                modified_smiles=None,
                modified_mol=None,
                success=False,
                message="Failed to sanitize modified molecule."
            )

        return ModificationResult(
            applied_rule="add_aromatic_ring",
            original_smiles=smiles,
            modified_smiles=modified_smiles,
            modified_mol=combined,
            success=True,
            message="Phenyl fragment added as prototype modification."
        )
    except Exception as e:
        return ModificationResult(
            applied_rule="add_aromatic_ring",
            original_smiles=smiles,
            modified_smiles=None,
            modified_mol=None,
            success=False,
            message=str(e)
        )
def modify_add_flexible_ether_linker(smiles: str) -> ModificationResult:
    try:
        mol = mol_from_smiles(smiles)
        if mol is None:
            return ModificationResult(
                applied_rule="add_flexible_ether_linker",
                original_smiles=smiles,
                modified_smiles=None,
                modified_mol=None,
                success=False,
                message="Invalid original SMILES."
            )

        ether_frag = Chem.MolFromSmiles("COC")
        combined = Chem.CombineMols(mol, ether_frag)
        modified_smiles = mol_to_smiles_safe(combined)

        if modified_smiles is None:
            return ModificationResult(
                applied_rule="add_flexible_ether_linker",
                original_smiles=smiles,
                modified_smiles=None,
                modified_mol=None,
                success=False,
                message="Failed to sanitize modified molecule."
            )

        return ModificationResult(
            applied_rule="add_flexible_ether_linker",
            original_smiles=smiles,
            modified_smiles=modified_smiles,
            modified_mol=combined,
            success=True,
            message="Flexible ether fragment added as prototype modification."
        )
    except Exception as e:
        return ModificationResult(
            applied_rule="add_flexible_ether_linker",
            original_smiles=smiles,
            modified_smiles=None,
            modified_mol=None,
            success=False,
            message=str(e)
        )
def modify_add_long_aliphatic_spacer(smiles: str) -> ModificationResult:
    try:
        mol = mol_from_smiles(smiles)
        if mol is None:
            return ModificationResult(
                applied_rule="add_long_aliphatic_spacer",
                original_smiles=smiles,
                modified_smiles=None,
                modified_mol=None,
                success=False,
                message="Invalid original SMILES."
            )

        spacer = Chem.MolFromSmiles("CCCC")
        combined = Chem.CombineMols(mol, spacer)
        modified_smiles = mol_to_smiles_safe(combined)

        if modified_smiles is None:
            return ModificationResult(
                applied_rule="add_long_aliphatic_spacer",
                original_smiles=smiles,
                modified_smiles=None,
                modified_mol=None,
                success=False,
                message="Failed to sanitize modified molecule."
            )

        return ModificationResult(
            applied_rule="add_long_aliphatic_spacer",
            original_smiles=smiles,
            modified_smiles=modified_smiles,
            modified_mol=combined,
            success=True,
            message="Aliphatic spacer fragment added as prototype modification."
        )
    except Exception as e:
        return ModificationResult(
            applied_rule="add_long_aliphatic_spacer",
            original_smiles=smiles,
            modified_smiles=None,
            modified_mol=None,
            success=False,
            message=str(e)
        )
def modify_add_polar_rigid_group(smiles: str) -> ModificationResult:
    try:
        mol = mol_from_smiles(smiles)
        if mol is None:
            return ModificationResult(
                applied_rule="add_polar_rigid_group",
                original_smiles=smiles,
                modified_smiles=None,
                modified_mol=None,
                success=False,
                message="Invalid original SMILES."
            )

        frag = Chem.MolFromSmiles("NC(=O)N")
        combined = Chem.CombineMols(mol, frag)
        modified_smiles = mol_to_smiles_safe(combined)

        if modified_smiles is None:
            return ModificationResult(
                applied_rule="add_polar_rigid_group",
                original_smiles=smiles,
                modified_smiles=None,
                modified_mol=None,
                success=False,
                message="Failed to sanitize modified molecule."
            )

        return ModificationResult(
            applied_rule="add_polar_rigid_group",
            original_smiles=smiles,
            modified_smiles=modified_smiles,
            modified_mol=combined,
            success=True,
            message="Polar rigid fragment added as prototype modification."
        )
    except Exception as e:
        return ModificationResult(
            applied_rule="add_polar_rigid_group",
            original_smiles=smiles,
            modified_smiles=None,
            modified_mol=None,
            success=False,
            message=str(e)
        )
def apply_rule_to_smiles(smiles: str, rule_name: str) -> ModificationResult:
    if rule_name == "add_aromatic_ring":
        return modify_add_aromatic_ring(smiles)

    elif rule_name == "add_flexible_ether_linker":
        return modify_add_flexible_ether_linker(smiles)

    elif rule_name == "add_long_aliphatic_spacer":
        return modify_add_long_aliphatic_spacer(smiles)

    elif rule_name == "add_polar_rigid_group":
        return modify_add_polar_rigid_group(smiles)
   

    else:
        return ModificationResult(
            applied_rule=rule_name,
            original_smiles=smiles,
            modified_smiles=smiles,
            modified_mol=mol_from_smiles(smiles),
            success=False,
            message=f"No modification function implemented yet for rule: {rule_name}"
        )

def refine_and_evaluate_tg(
    monomer_1: str,
    monomer_2: str,
    predicted_tg: float,
    target_tg: float,
    tg_predictor: callable,
    threshold: float = 5.0,
    top_k: int = 4
) -> TgRefinementResult:
    """
    1. Decide Tg rule
    2. Pick top rule
    3. Modify one monomer
    4. Predict new Tg
    5. Compare improvement
    """

    decision = decide_tg_rules(
        monomer_1=monomer_1,
        monomer_2=monomer_2,
        predicted_tg=predicted_tg,
        target_tg=target_tg,
        threshold=threshold,
        top_k=top_k
    )

    if decision.direction == "keep" or not decision.suggestions:
        return TgRefinementResult(
            original_monomer_1=monomer_1,
            original_monomer_2=monomer_2,
            modified_monomer_1=monomer_1,
            modified_monomer_2=monomer_2,
            applied_rule="none",
            original_predicted_tg=predicted_tg,
            new_predicted_tg=predicted_tg,
            tg_improvement=0.0,
            target_tg=target_tg,
            reached_target=abs(target_tg - predicted_tg) <= threshold,
        )

    #top_rule = decision.suggestions[0].rule_name
    #monomer_index = choose_monomer_to_modify(monomer_1, monomer_2, top_rule)

    applied = apply_best_available_rule(monomer_1, monomer_2, decision.suggestions)
    if applied is None:
        return TgRefinementResult(
            original_monomer_1=monomer_1,
            original_monomer_2=monomer_2,
            modified_monomer_1=monomer_1,
            modified_monomer_2=monomer_2,
            applied_rule="none",
            original_predicted_tg=predicted_tg,
            
        )
    

    new_m1 = applied["new_m1"]
    new_m2 = applied["new_m2"]
    top_rule = applied["rule_name"]

    return TgRefinementResult(
        original_monomer_1=monomer_1,
        original_monomer_2=monomer_2,
        modified_monomer_1=new_m1,
        modified_monomer_2=new_m2,
        applied_rule=top_rule,
        original_predicted_tg=predicted_tg,
        #new_predicted_tg=new_predicted_tg,
        #tg_improvement=tg_improvement,
        #target_tg=target_tg,
        #reached_target=new_error <= threshold,
    )

