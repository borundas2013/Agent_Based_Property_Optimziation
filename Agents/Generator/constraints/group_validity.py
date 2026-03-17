import sys
import os



# Import from same package using absolute import
from constraints.groups import ChemicalGroupAnalyzer

class GroupCheck:
    def __init__(self):
        self.analyzer = ChemicalGroupAnalyzer()

    def check_exact_group_consistency(self, smiles1: str, smiles2: str, group1: str, group2: str) -> float:
        try:
            group_1_ok, group_2_ok = self.analyzer.check_group_consistency(group1, group2, smiles1, smiles2)
            
            reverse_group_1_ok, reverse_group_2_ok = self.analyzer.check_group_consistency(group2, group1, smiles1, smiles2)
            
            if group_1_ok and group_2_ok:
                return True
            elif reverse_group_1_ok and reverse_group_2_ok:
                return True
            else:
                return False
        except Exception as e:
            print(f"[Group check failed] {e}")
            return False
    def check_partial_group_consistency(self, smiles1: str, smiles2: str, group1: str, group2: str) -> float:
        try:
            group_1_ok, group_2_ok = self.analyzer.check_group_consistency(group1, group2, smiles1, smiles2)
            reverse_group_1_ok, reverse_group_2_ok = self.analyzer.check_group_consistency(group2, group1, smiles1, smiles2)
            if group_1_ok or group_2_ok:
                return True
            elif reverse_group_1_ok or reverse_group_2_ok:
                return True
            else:
                return False
        except Exception as e:
            print(f"[Group check failed] {e}")
            return False
  
        

if __name__ == "__main__":
    reward = GroupCheck()
    smiles1 = "CCOCCOC2OC2"
    smiles2 = "NCCCOCCNC"

    group1 = "C=C"
    group2 = "NC"

    print(reward.check_exact_group_consistency(smiles1, smiles2, group1, group2))
    print(reward.check_partial_group_consistency(smiles1, smiles2, group1, group2))
    