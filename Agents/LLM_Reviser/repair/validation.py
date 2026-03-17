import json
from typing import Any, Dict

from rdkit import Chem
from rdkit.Chem import DataStructs
from rdkit.Chem.AllChem import GetMorganFingerprintAsBitVect

from Generator.constraints.groups import ChemicalGroupAnalyzer


def safe_parse_llm_output(raw_text: str) -> Dict[str, Any]:
    try:
        data = json.loads(raw_text)
        if not isinstance(data, dict):
            return {
                "ok": False,
                "error": "LLM output is not a JSON object",
                "data": None,
            }
        return {"ok": True, "error": None, "data": data}
    except Exception as e:
        return {"ok": False, "error": f"JSON parse error: {str(e)}", "data": None}


def validate_smiles(smiles: str):
    if not smiles or not isinstance(smiles, str):
        return False, None

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return False, None

    try:
        Chem.SanitizeMol(mol)
    except Exception:
        return False, None

    canonical = Chem.MolToSmiles(mol)
    return True, canonical


def has_reaction_constraints(monomer_1: str, monomer_2: str):
    analyzer = ChemicalGroupAnalyzer()
    return analyzer.check_reaction_consistency(monomer_1, monomer_2)


def compute_similarity(sm1: str, sm2: str) -> float:
    mol1 = Chem.MolFromSmiles(sm1)
    mol2 = Chem.MolFromSmiles(sm2)
    if mol1 is None or mol2 is None:
        return 0.0

    fp1 = GetMorganFingerprintAsBitVect(mol1, 2, nBits=2048)
    fp2 = GetMorganFingerprintAsBitVect(mol2, 2, nBits=2048)

    return DataStructs.TanimotoSimilarity(fp1, fp2)


def validate_revised_candidate(revised_m1, revised_m2):
    result = {
        "valid": True,
        "errors": [],
        "canonical": {},
    }

    # 1. SMILES validation
    v1, c1 = validate_smiles(revised_m1)
    v2, c2 = validate_smiles(revised_m2)

    if not v1:
        result["valid"] = False
        result["errors"].append("invalid_monomer_1")
    if not v2:
        result["valid"] = False
        result["errors"].append("invalid_monomer_2")

    if not result["valid"]:
        return result

    result["canonical"]["monomer_1"] = c1
    result["canonical"]["monomer_2"] = c2

    # 2. Reactive preservation
    has_reaction, pattern1, pattern2 = has_reaction_constraints(revised_m1, revised_m2)
    if not has_reaction:
        result["valid"] = False
        result["errors"].append(
            "No Reaction Constraints. Both monomers should have compatibale functional groups"
            + "such as vinyl-vinyl, epoxy-imine, imine-epoxy, thiol-vinyl, hydroxyl-vinyl, acrylate-vinyl, etc."
        )
        return result

    # Optional similarity checks (currently disabled in original code).
    # sim1 = compute_similarity(c1, pattern1)
    # sim2 = compute_similarity(c2, pattern2)
    # if sim1 < 0.8 or sim2 < 0.8:
    #     result["valid"] = False
    #     result["errors"].append("low_similarity")

    return result

