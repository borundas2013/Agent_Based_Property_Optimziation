from rdkit import Chem
from constraints.smile_common_issue_fix import fix_smiles_parsing_issues,detect_and_fix_dangling_rings


class ChemicalValidityCheck:
    """
    Chemical validity reward for two-monomer polymer generation.

    Design:
    - Returns a gate value in [0, 1]
    - 1.0 → both SMILES are chemically valid
    - 0.0 → at least one SMILES is invalid
    """

    def __init__(self, allow_disconnected: bool = False):
        """
        Parameters
        ----------
        allow_disconnected : bool
            If False, SMILES containing '.' (multiple fragments) are treated as invalid.
        """
        self.allow_disconnected = allow_disconnected

    def _is_valid_smiles(self, smiles: str) -> bool:
       
        if smiles is None or not isinstance(smiles, str):
            return False, None

        smiles = smiles.strip()
        if len(smiles) == 0:
            return False, None

      
        if not self.allow_disconnected and "." in smiles:
            return False, None

        # First attempt: direct parse
        try:
            mol = Chem.MolFromSmiles(smiles)
        except Exception:
            mol = None

        # If parsing fails, try our SMILES fixers sequentially
        if mol is None:
            smiles = fix_smiles_parsing_issues(smiles)
            try:
                mol = Chem.MolFromSmiles(smiles)
            except Exception:
                mol = None

            if mol is None:
                smiles = detect_and_fix_dangling_rings(smiles)
                try:
                    mol = Chem.MolFromSmiles(smiles)
                except Exception:
                    mol = None

            if mol is None:
                return False, None

        try:
            Chem.SanitizeMol(mol)
        except Exception:
            return False, None

        return True, smiles

    def check_chemical_validity(self, monomer_1: str, monomer_2: str) -> float:
        valid_1, smiles_1 = self._is_valid_smiles(monomer_1)
        valid_2, smiles_2 = self._is_valid_smiles(monomer_2)
        return valid_1 and valid_2, smiles_1, smiles_2


if __name__ == "__main__":
    reward = ChemicalValidityCheck()
    print(reward.check_chemical_validity("C1OC1CCC", "C1CC2"))
