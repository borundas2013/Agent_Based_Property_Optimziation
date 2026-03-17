from __future__ import annotations
from typing import Deque, Optional, List, Tuple
from collections import deque
import os, sys

from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', '..')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(current_dir))))
print(project_root)
data_path = os.path.join(project_root, "RLHF_TSMP", "data", 'unique_smiles_Er.csv')#"/ddnB/work/borun22/RLHF/data/unique_smiles_Er.csv"#
from Utils import is_valid_smiles, mol, scaffold, load_smiles_data, canon

def _mol(smiles: str):
    try:
        return Chem.MolFromSmiles(smiles)
    except Exception:
        return None

def _fp(mol, radius=2, nbits=2048):
    return AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=nbits)

def _pair_fp(sm1: str, sm2: str, radius=2, nbits=2048):
    m1, m2 = _mol(sm1), _mol(sm2)
    if m1 is None or m2 is None:
        return None
    fp1 = _fp(m1, radius, nbits)
    fp2 = _fp(m2, radius, nbits)
    fp1 |= fp2
    return fp1

class TrainingDistanceDiversity:
    """
    Diversity wrt training set:
      max_sim = max Tanimoto similarity(new_pair_fp, training_pair_fps)
      reward_continuous = 1 - max_sim in [0,1]
      reward_discrete in {-1,0,1} using thresholds
    """

    def __init__(
        self,
        radius: int = 2,
        nbits: int = 2048,
    ):
        self.training_pairs = get_training_pairs()
        self.radius = radius
        self.nbits = nbits
        self.ref_fps = []
        for a, b in self.training_pairs:
            f = _pair_fp(a, b, radius, nbits)
            if f is not None:
                self.ref_fps.append(f)

    def max_sim_to_training(self, sm1: str, sm2: str) -> float:
        fnew = _pair_fp(sm1, sm2, self.radius, self.nbits)
        if fnew is None or len(self.ref_fps) == 0:
            return 1.0  # treat invalid as "not diverse"; but we will gate to neutral in reward
        sims = DataStructs.BulkTanimotoSimilarity(fnew, self.ref_fps)
        return float(max(sims))

    def check_diversity_continuous(self, sm1: str, sm2: str) -> float:
        fnew = _pair_fp(sm1, sm2, self.radius, self.nbits)
        if fnew is None or len(self.ref_fps) == 0:
            return 0.0  # neutral (validity reward handles invalid)
        max_sim = float(max(DataStructs.BulkTanimotoSimilarity(fnew, self.ref_fps)))
        return max_sim  # [0,1]

    def check_diversity_discrete(self, sm1: str, sm2: str, hi: float = 0.85, mid: float = 0.70) -> float:
        fnew = _pair_fp(sm1, sm2, self.radius, self.nbits)
        if fnew is None or len(self.ref_fps) == 0:
            return 0.0  # neutral
        max_sim = float(max(DataStructs.BulkTanimotoSimilarity(fnew, self.ref_fps)))
        print(max_sim)
        if max_sim >= hi:
            return -1.0
        if max_sim >= mid:
            return 0.5
        return 1.0


    
def get_training_pairs() -> List[Tuple[str, str]]:
    smiles1_list, smiles2_list = load_smiles_data(data_path)
    return [(smiles1, smiles2) for smiles1, smiles2 in zip(smiles1_list, smiles2_list)]



if __name__ == "__main__":
    smiles_lists = get_training_pairs()
    print(len(smiles_lists))
    test_smiles1 = smiles_lists[0][0]
    test_smiles2 = smiles_lists[0][1]

    div = TrainingDistanceDiversity()
    diversity_reward = div.check_diversity_continuous(test_smiles1+"CCCC", test_smiles2)
    print(diversity_reward)

    diversity_reward = div.check_diversity_discrete(test_smiles1+"CCCC", test_smiles2)
    print(diversity_reward)
